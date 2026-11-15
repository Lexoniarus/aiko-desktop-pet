import { Container, Graphics, Sprite, Texture } from 'pixi.js';
import {
  artworkAttachments,
  artworkFurniture,
  artworkFurnitureFrame,
  artworkTabletopInset,
  artworkWallScale,
} from './RoomArtwork';
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
    window?: Sprite;
  }> = [];
  private floor = new Graphics();
  private furniture: Array<{
    view: Sprite;
    item: FurniturePlacement;
    attachment?: Sprite;
  }> = [];
  private readonly usesRoomArtwork: boolean;
  private lastVersion = -1;
  constructor(
    world: Container,
    layout: RoomLayout,
    images: Record<string, HTMLImageElement>,
    onFridgeTap: () => void,
  ) {
    const wallArtwork = images.wall && Texture.from(images.wall);
    const windowArtwork = images.window && Texture.from(images.window);
    this.usesRoomArtwork = Boolean(wallArtwork);
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
        texture =
          wallArtwork ??
          Texture.from(
            wall.asset === 'living'
              ? roomBackground(images.kitchen!, images[wall.asset])
              : roomBackground(images[wall.asset]!),
          );
        textures.set(wall.asset, texture);
      }
      const span =
        wall.id === 'north' || wall.id === 'south' ? 2 * corner : Math.PI - 2 * corner;
      for (const repeat of [-1, 0, 1]) {
        const view = new Sprite(texture);
        view.anchor.set(0.5, 0);
        view.zIndex = -10000;
        world.addChild(view);
        const panel = { view, bearing: wallBearings[wall.id]!, span, repeat };
        if (windowArtwork && wall.id === 'east') {
          const window = new Sprite(windowArtwork);
          window.anchor.set(0.5, 1);
          window.zIndex = -9998;
          world.addChild(window);
          this.panels.push({ ...panel, window });
        } else {
          this.panels.push(panel);
        }
      }
    }
    this.floor.zIndex = -9999;
    world.addChild(this.floor);
    const furniture = wallArtwork ? artworkFurniture(layout, images) : layout.furniture;
    for (const item of furniture) {
      const [x, y, width, height] = item.crop;
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(images[item.asset]!, x, y, width, height, 0, 0, width, height);
      const view = new Sprite(Texture.from(canvas));
      view.anchor.set(...item.pivot);
      if (item.id === 'fridge') {
        const pixels = ctx.getImageData(0, 0, width, height).data;
        view.eventMode = 'static';
        view.hitArea = {
          contains: (px: number, py: number) => {
            const ix = Math.floor(px + width * item.pivot[0]);
            const iy = Math.floor(py + height * item.pivot[1]);
            return (
              ix >= 0 &&
              ix < width &&
              iy >= 0 &&
              iy < height &&
              pixels[(iy * width + ix) * 4 + 3]! >= 32
            );
          },
        };
        view.cursor = 'pointer';
        view.on('pointertap', onFridgeTap);
      }
      world.addChild(view);
      const prop = wallArtwork && artworkAttachments[item.id];
      if (prop) {
        const attachment = new Sprite(Texture.from(images[prop.asset]!));
        attachment.anchor.set(0.5, 1);
        world.addChild(attachment);
        this.furniture.push({ view, item, attachment });
      } else {
        this.furniture.push({ view, item });
      }
    }
  }
  furnitureFrame(id: string, projection: RoomProjection) {
    const item = this.furniture.find((entry) => entry.item.id === id)?.item;
    return item && this.projectFurniture(projection, item);
  }

  private projectFurniture(projection: RoomProjection, item: FurniturePlacement) {
    const frame = this.usesRoomArtwork
      ? artworkFurnitureFrame(projection, item)
      : furnitureFrame(projection, item);
    if (this.usesRoomArtwork && item.id === 'table') {
      frame.surface.y += frame.height * artworkTabletopInset;
    }
    return frame;
  }

  update(camera: RoomCamera): void {
    if (camera.version === this.lastVersion) return;
    this.lastVersion = camera.version;
    const projection = camera.projection;
    const { floorLine, angularScale, width } = projection;
    this.drawFloor(projection);
    for (const { view, bearing, span, repeat, window } of this.panels) {
      const center = projection.screenX(bearing) + repeat * Math.PI * 2 * angularScale;
      const panelWidth = span * angularScale;
      view.position.set(center, 0);
      // A subpixel overlap sits under the common skirting and corner lines.
      view.setSize(panelWidth + 1, floorLine + 1);
      if (window) {
        const height = Math.min(
          floorLine * 0.92,
          (panelWidth * 0.8 * window.texture.height) / window.texture.width,
        );
        window.position.set(center, floorLine);
        window.scale.set(height / window.texture.height);
      }
      const joint = center - panelWidth / 2;
      if (joint >= 0 && joint <= width) {
        const seamWidth = Math.max(1, 2.5 * projection.fit);
        this.floor.rect(joint - seamWidth / 2, 0, seamWidth, floorLine).fill({
          color: 0x8d7eac,
          alpha: 0.5,
        });
      }
    }
    for (const { view, item, attachment } of this.furniture) {
      const frame = this.projectFurniture(projection, item);
      view.position.set(frame.x, frame.y);
      const flipX = frame.flipX && !this.usesRoomArtwork;
      view.scale.set(frame.scale * (flipX ? -1 : 1), frame.scale);
      view.zIndex = frame.order;
      if (attachment) {
        const prop = artworkAttachments[item.id]!;
        attachment.position.set(
          frame.x + frame.width * prop.offsetX,
          prop.wallOffset === undefined
            ? frame.y + frame.height * ((prop.offsetY ?? 0) - 1)
            : projection.floorLine + prop.wallOffset * artworkWallScale(projection),
        );
        attachment.scale.set((frame.width * prop.width) / attachment.texture.width);
        attachment.zIndex = frame.order + 0.000001;
      }
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
