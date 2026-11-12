import { Container, Graphics, Sprite, Texture } from 'pixi.js';
import type { RoomCamera } from './RoomCamera';
import type { FurniturePlacement, RoomLayout } from './RoomLayout';
import { furnitureFrame } from './RoomPresentation';
import { roomBackground } from './RoomBackground';
import type { RoomProjection } from './RoomProjection';

/** The grid owns placement; artwork stays flat with its original proportions. */
export class RoomScene {
  private panels: Array<{
    view: Sprite;
    bearing: number;
    span: number;
    repeat: number;
  }> = [];
  private floor = new Graphics();
  private furniture: Array<{
    view: Sprite;
    item: FurniturePlacement;
  }> = [];
  private lastVersion = -1;
  constructor(
    world: Container,
    layout: RoomLayout,
    images: Record<string, HTMLImageElement>,
    onFridgeTap: () => void,
  ) {
    const wallBearings: Record<string, number> = {
      north: 0,
      east: Math.PI / 2,
      south: Math.PI,
      west: -Math.PI / 2,
    };
    const corner = Math.atan2(layout.width, layout.depth);
    const textures = new Map<string, Texture>();
    for (const wall of layout.walls) {
      let texture = textures.get(wall.asset);
      if (!texture) {
        const artwork = images[wall.asset]!;
        const canvas =
          wall.asset === 'living'
            ? roomBackground(images.kitchen!, artwork)
            : roomBackground(artwork);
        texture = Texture.from(canvas);
        textures.set(wall.asset, texture);
      }
      const span =
        wall.id === 'north' || wall.id === 'south' ? 2 * corner : Math.PI - 2 * corner;
      for (const repeat of [-1, 0, 1]) {
        const view = new Sprite(texture);
        view.anchor.set(0.5, 0);
        view.zIndex = -10000;
        world.addChild(view);
        this.panels.push({ view, bearing: wallBearings[wall.id]!, span, repeat });
      }
    }
    this.floor.zIndex = -9999;
    world.addChild(this.floor);
    for (const item of layout.furniture) {
      const [x, y, width, height] = item.crop;
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(images[item.asset]!, x, y, width, height, 0, 0, width, height);
      const pixels = ctx.getImageData(0, 0, width, height).data;
      const view = new Sprite(Texture.from(canvas));
      view.anchor.set(...item.pivot);
      view.eventMode = 'static';
      view.hitArea = {
        contains: (px: number, py: number) => {
          const ix = Math.floor(px + width * item.pivot[0]),
            iy = Math.floor(py + height * item.pivot[1]);
          return (
            ix >= 0 &&
            ix < width &&
            iy >= 0 &&
            iy < height &&
            pixels[(iy * width + ix) * 4 + 3]! >= 32
          );
        },
      };
      if (item.id === 'fridge') {
        view.cursor = 'pointer';
        view.on('pointertap', onFridgeTap);
      }
      world.addChild(view);
      this.furniture.push({ view, item });
    }
  }
  update(camera: RoomCamera): void {
    if (camera.version === this.lastVersion) return;
    this.lastVersion = camera.version;
    const projection = camera.projection;
    const { floorLine, angularScale, width } = projection;
    this.drawFloor(projection);
    for (const { view, bearing, span, repeat } of this.panels) {
      const center = projection.screenX(bearing) + repeat * Math.PI * 2 * angularScale;
      const panelWidth = span * angularScale;
      view.position.set(center, 0);
      // A subpixel overlap sits under the common skirting and corner lines.
      view.setSize(panelWidth + 1, floorLine + 1);
      const joint = center - panelWidth / 2;
      if (joint >= 0 && joint <= width) {
        const seamWidth = Math.max(1, 2.5 * projection.fit);
        this.floor.rect(joint - seamWidth / 2, 0, seamWidth, floorLine).fill({
          color: 0x8d7eac,
          alpha: 0.5,
        });
      }
    }
    for (const { view, item } of this.furniture) {
      const frame = furnitureFrame(projection, item);
      view.position.set(frame.x, frame.y);
      view.scale.set(frame.scale * (frame.flipX ? -1 : 1), frame.scale);
      view.zIndex = frame.order;
    }
  }

  private drawFloor(projection: RoomProjection): void {
    const { width, height, floorLine } = projection;
    const floor = this.floor.clear();
    floor.rect(0, floorLine, width, height - floorLine).fill(0xeac6a7);
    const skirtingHeight = Math.min(floorLine, 12 * projection.fit);
    floor.rect(0, floorLine - skirtingHeight, width, skirtingHeight).fill(0xc2aabd);
    // The floor is one strip. Its staggered joints share the panorama's turn.
    const rowHeight = Math.max(1, 54 * projection.fit);
    const plankWidth = (Math.PI * 2 * projection.angularScale) / 24;
    const origin = projection.screenX(0);
    for (let row = 0, y = floorLine; y < height; row++, y += rowHeight) {
      floor.moveTo(0, y).lineTo(width, y);
      const phase = origin + ((row % 2) * plankWidth) / 2;
      for (
        let x = ((phase % plankWidth) + plankWidth) % plankWidth;
        x < width;
        x += plankWidth
      ) {
        floor.moveTo(x, y).lineTo(x, Math.min(height, y + rowHeight));
      }
    }
    floor.stroke({ color: 0xc39a7d, width: 1, alpha: 0.62 });
  }
}
