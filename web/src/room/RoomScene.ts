import { Container, Sprite, Texture } from 'pixi.js';
import type { RoomCamera } from './RoomCamera';
import type { FurniturePlacement, RoomLayout, RoomPoint } from './RoomLayout';

/** The grid owns placement; artwork stays flat with its original proportions. */
export class RoomScene {
  private panels: Array<{ view: Sprite; bearing: number; repeat: number }> = [];
  private furniture: Array<{
    view: Sprite;
    item: FurniturePlacement;
    point: RoomPoint;
  }> = [];
  private lastVersion = -1;
  constructor(
    world: Container,
    layout: RoomLayout,
    images: Record<string, HTMLImageElement>,
  ) {
    const wallBearings: Record<string, number> = {
      north: 0,
      east: Math.PI / 2,
      south: Math.PI,
      west: -Math.PI / 2,
    };
    // Four adjoining 2D panels. Shared skirting/floor keep the joins level.
    for (const [index, wall] of layout.walls.entries()) {
      const canvas = document.createElement('canvas');
      canvas.width = 1800;
      canvas.height = 900;
      const ctx = canvas.getContext('2d')!,
        source = images[wall.asset]!,
        floor = images.kitchen!;
      ctx.drawImage(
        source,
        0,
        0,
        source.width,
        (source.height * 760) / 900,
        0,
        0,
        1800,
        654,
      );
      ctx.drawImage(
        floor,
        0,
        (floor.height * 760) / 900,
        floor.width,
        (floor.height * 42) / 900,
        0,
        654,
        1800,
        36,
      );
      ctx.save();
      if (index % 2) {
        ctx.translate(1800, 0);
        ctx.scale(-1, 1);
      }
      ctx.drawImage(
        floor,
        0,
        (floor.height * 802) / 900,
        floor.width,
        (floor.height * 98) / 900,
        0,
        690,
        1800,
        210,
      );
      ctx.restore();
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
      world.addChild(view);
      const point = { x: item.x, depth: item.z };
      // The same occupied footprint support edge as the grid renderer.
      if (item.wall === 'north') point.depth += item.depth / 2;
      else if (item.wall === 'south') point.depth -= item.depth / 2;
      else if (item.wall === 'east') point.x -= item.width / 2;
      else if (item.wall === 'west') point.x += item.width / 2;
      else if (
        Math.abs(layout.width / 2 - item.x) > Math.abs(layout.depth / 2 - item.z)
      )
        point.x += (Math.sign(layout.width / 2 - item.x) * item.width) / 2;
      else point.depth += (Math.sign(layout.depth / 2 - item.z) * item.depth) / 2;
      this.furniture.push({ view, item, point });
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
    for (const { view, item, point } of this.furniture) {
      const ground = projection.projectPoint(point, item.elevation);
      view.position.set(ground.x, ground.y);
      view.scale.set((item.height * ground.scale) / item.crop[3]);
      view.zIndex = -ground.depth;
    }
  }
}
