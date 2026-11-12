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
    for (const wall of layout.walls) {
      const canvas = roomBackground(images[wall.asset]!, wall.asset === 'living');
      const texture = Texture.from(canvas);
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
    const wallHeight = Math.max(
      1,
      Math.min(
        projection.height,
        projection.yAt(Math.min(projection.layout.width, projection.layout.depth) / 2),
      ),
    );
    for (const { view, bearing, span, repeat } of this.panels) {
      view.position.set(
        projection.screenX(bearing) + repeat * Math.PI * 2 * projection.angularScale,
        0,
      );
      view.setSize(span * projection.angularScale + 1, wallHeight + 1);
    }
    this.drawFloor(projection);
    for (const { view, item } of this.furniture) {
      const frame = furnitureFrame(projection, item);
      view.position.set(frame.x, frame.y);
      view.scale.set(frame.scale * (frame.flipX ? -1 : 1), frame.scale);
      view.zIndex = frame.order;
    }
  }

  private drawFloor(projection: RoomProjection): void {
    const { width, height } = projection;
    const floor = this.floor.clear();
    const count = Math.ceil(width / 10);
    const edge = Array.from({ length: count + 1 }, (_, index) => {
      const x = (index * width) / count;
      return { x, distance: projection.wallDistanceAt(x) };
    });
    const rim = edge.map(({ x, distance }) => ({
      x,
      y: Math.min(height, projection.yAt(distance)),
    }));
    floor.poly([...rim, { x: width, y: height }, { x: 0, y: height }]).fill(0xeac6a7);
    for (const [elevation, color, thickness] of [
      [0, 0xb78e7a, 2],
      [6, 0xc2aabd, 2],
    ] as const) {
      for (const [index, { x, distance }] of edge.entries()) {
        const y = projection.yAt(distance, elevation);
        if (index) floor.lineTo(x, y);
        else floor.moveTo(x, y);
      }
      floor.stroke({ color, width: thickness });
    }
    // Draw a single staggered plank pattern in floor coordinates across every wall.
    for (let distance = 132; distance < 500; distance += 22) {
      const y = projection.yAt(distance);
      const previous = projection.yAt(distance - 22);
      if (y >= height) continue;
      for (let i = 1; i < rim.length; i++) {
        const a = rim[i - 1]!;
        const b = rim[i]!;
        if (y >= a.y && y >= b.y) floor.moveTo(a.x, y).lineTo(b.x, y);
      }
      const angularStep = (Math.PI * 2) / 48;
      const phase = Math.round((distance - 132) / 22) % 2 ? angularStep / 2 : 0;
      for (let index = 0; index < 48; index++) {
        const x = projection.screenX(index * angularStep + phase);
        if (x < 0 || x > width || distance > projection.wallDistanceAt(x)) continue;
        floor.moveTo(x, y).lineTo(x, Math.min(height, previous));
      }
    }
    floor.stroke({ color: 0xc39a7d, width: 1, alpha: 0.62 });
  }
}
