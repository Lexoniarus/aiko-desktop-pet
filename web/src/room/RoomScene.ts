import { Container, Sprite, Texture } from 'pixi.js';
import type { RoomCamera } from './RoomCamera';
import type { FurniturePlacement, RoomLayout } from './RoomLayout';
import { furnitureFrame } from './RoomPresentation';
import { roomBackground } from './RoomBackground';

/** The grid owns placement; artwork stays flat with its original proportions. */
export class RoomScene {
  private panels: Array<{ view: Sprite; bearing: number; repeat: number }> = [];
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
    // Four adjoining 2D panels. Shared skirting/floor keep the joins level.
    for (const [index, wall] of layout.walls.entries()) {
      const canvas = roomBackground(
        images[wall.asset]!,
        images.kitchen!,
        wall.asset === 'living',
        index % 2 !== 0,
      );
      const texture = Texture.from(canvas);
      for (const repeat of [-1, 0, 1]) {
        const view = new Sprite(texture);
        view.anchor.set(0.5, 0);
        view.zIndex = -10000;
        world.addChild(view);
        this.panels.push({ view, bearing: wallBearings[wall.id]!, repeat });
      }
    }
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
    for (const { view, bearing, repeat } of this.panels) {
      view.position.set(
        projection.screenX(bearing) +
          repeat * projection.panelWidth * 4 * projection.fit,
        0,
      );
      view.scale.set(projection.fit);
    }
    for (const { view, item } of this.furniture) {
      const frame = furnitureFrame(projection, item);
      view.position.set(frame.x, frame.y);
      view.scale.set(frame.scale * (frame.flipX ? -1 : 1), frame.scale);
      view.zIndex = frame.order;
    }
  }
}
