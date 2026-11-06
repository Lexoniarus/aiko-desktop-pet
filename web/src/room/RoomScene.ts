import { Container, Graphics, Mesh, MeshGeometry, Texture } from 'pixi.js';
import type { RoomCamera } from './RoomCamera';
import type { FurniturePlacement, RoomLayout, RoomPoint } from './RoomLayout';

/** Static room art shares its ground anchors with Python's occupied footprints. */
export class RoomScene {
  private floor = new Graphics();
  private walls: Array<{ mesh: Mesh<MeshGeometry>; wall: string }> = [];
  private furniture: Array<{
    view: Mesh<MeshGeometry>;
    item: FurniturePlacement;
  }> = [];
  private lastVersion = -1;
  private camera?: RoomCamera;
  private hitMasks = new Map<
    string,
    { alpha: Uint8Array; width: number; height: number }
  >();
  private faces = new Map<
    string,
    { point: RoomPoint; alongZ: boolean; width: number }
  >();
  constructor(
    private world: Container,
    private layout: RoomLayout,
    images: Record<string, HTMLImageElement>,
  ) {
    this.floor.zIndex = -10000;
    world.addChild(this.floor);
    for (const wallDefinition of layout.walls) {
      const wall = wallDefinition.id,
        source = images[wallDefinition.asset]!;
      const canvas = document.createElement('canvas');
      canvas.width = 1600;
      canvas.height = 750;
      canvas
        .getContext('2d')!
        .drawImage(
          source,
          0,
          source.height * 0.06,
          source.width,
          source.height * 0.83,
          0,
          0,
          1600,
          750,
        );
      const mesh = new Mesh({
        geometry: new MeshGeometry({
          positions: new Float32Array(),
          uvs: new Float32Array(),
          indices: new Uint32Array(),
        }),
        texture: Texture.from(canvas),
      });
      mesh.zIndex = -9000;
      world.addChild(mesh);
      this.walls.push({ mesh, wall });
    }
    for (const item of layout.furniture) {
      const [x, y, w, h] = item.crop;
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      canvas.getContext('2d')!.drawImage(images[item.asset]!, x, y, w, h, 0, 0, w, h);
      const texture = Texture.from(canvas);
      const rgba = canvas.getContext('2d')!.getImageData(0, 0, w, h).data;
      const alpha = new Uint8Array(w * h);
      for (let i = 0; i < alpha.length; i++) alpha[i] = rgba[i * 4 + 3]!;
      this.hitMasks.set(item.id, { alpha, width: w, height: h });
      const view = new Mesh({
        geometry: new MeshGeometry({
          positions: new Float32Array(),
          uvs: new Float32Array(),
          indices: new Uint32Array(),
        }),
        texture,
      });
      view.eventMode = 'static';
      view.hitArea = { contains: (x: number, y: number) => this.opaqueAt(item, x, y) };
      world.addChild(view);
      this.furniture.push({ view, item });
    }
  }
  private opaqueAt(item: FurniturePlacement, x: number, y: number): boolean {
    const face = this.faces.get(item.id),
      mask = this.hitMasks.get(item.id);
    if (!this.camera || !face || !mask) return false;
    const ray = this.camera.projection.screenRay(x, y),
      axis = face.alongZ ? 0 : 2;
    const divisor = ray.direction[axis]!;
    if (Math.abs(divisor) < 1e-6) return false;
    const plane = face.alongZ ? face.point.x : face.point.depth;
    const t = (plane - ray.origin[axis]!) / divisor;
    if (t <= 0) return false;
    const alongAxis = face.alongZ ? 2 : 0;
    const along = ray.origin[alongAxis]! + t * ray.direction[alongAxis]!;
    const centre = face.alongZ ? face.point.depth : face.point.x;
    const u = (along - centre) / face.width + item.pivot[0];
    const v =
      item.pivot[1] -
      (ray.origin[1]! + t * ray.direction[1]! - item.elevation) / item.height;
    return (
      u >= 0 &&
      u < 1 &&
      v >= 0 &&
      v < 1 &&
      mask.alpha[
        Math.floor(v * mask.height) * mask.width + Math.floor(u * mask.width)
      ]! >= 32
    );
  }
  private wallPoint(wall: string, along: number, height: number): [RoomPoint, number] {
    const l = this.layout;
    if (wall === 'north') return [{ x: along, depth: 0 }, height];
    if (wall === 'east') return [{ x: l.width, depth: along }, height];
    if (wall === 'south') return [{ x: l.width - along, depth: l.depth }, height];
    return [{ x: 0, depth: l.depth - along }, height];
  }
  private surface(
    mesh: Mesh<MeshGeometry>,
    camera: RoomCamera,
    point: (u: number, v: number) => [RoomPoint, number],
    columns: number,
    rows: number,
  ): void {
    const positions: number[] = [],
      uvs: number[] = [],
      indices: number[] = [];
    for (let y = 0; y < rows; y++)
      for (let x = 0; x < columns; x++) {
        const corners = [
          [x / columns, y / rows],
          [(x + 1) / columns, y / rows],
          [(x + 1) / columns, (y + 1) / rows],
          [x / columns, (y + 1) / rows],
        ] as const;
        const projected = corners.map(([u, v]) =>
          camera.projection.projectPoint(...point(u, v)),
        );
        if (projected.some((p) => p.depth < 1)) continue;
        const offset = positions.length / 2;
        for (let i = 0; i < 4; i++) {
          positions.push(projected[i]!.x, projected[i]!.y);
          uvs.push(...corners[i]!);
        }
        indices.push(offset, offset + 1, offset + 2, offset, offset + 2, offset + 3);
      }
    mesh.geometry.uvs = new Float32Array(uvs);
    mesh.geometry.positions = new Float32Array(positions);
    mesh.geometry.indices = new Uint32Array(indices);
    mesh.visible = indices.length > 0;
  }
  update(camera: RoomCamera): void {
    if (camera.version === this.lastVersion) return;
    this.lastVersion = camera.version;
    this.camera = camera;
    const l = this.layout;
    this.floor.clear();
    // One floor across all four walls. Plank seams belong to world coordinates.
    const rowHeight = 25,
      plankWidth = 200;
    for (let row = 0, z = 0; z < l.depth; row++, z += rowHeight) {
      const offset = row % 2 ? -plankWidth / 2 : 0;
      for (let column = 0, x = offset; x < l.width; column++, x += plankWidth) {
        const left = Math.max(0, x),
          right = Math.min(l.width, x + plankWidth);
        const points = [
          [left, z],
          [right, z],
          [right, Math.min(l.depth, z + rowHeight)],
          [left, Math.min(l.depth, z + rowHeight)],
        ].map(([px, pz]) => camera.projection.projectPoint({ x: px!, depth: pz! }));
        if (points.some((p) => p.depth < 1)) continue;
        const colours = [0xd8bf9c, 0xd6bd9a, 0xdbc3a2];
        this.floor
          .poly(points.flatMap((p) => [p.x, p.y]))
          .fill(colours[(row + column) % 3]!)
          .stroke({ width: 0.6, color: 0xb79c7a, alpha: 0.35 });
      }
    }
    for (const { mesh, wall } of this.walls) {
      const length = wall === 'north' || wall === 'south' ? l.width : l.depth;
      this.surface(
        mesh,
        camera,
        (u, v) => this.wallPoint(wall, u * length, (1 - v) * l.wall_height),
        16,
        4,
      );
    }
    for (const { view, item } of this.furniture) {
      const point = { x: item.x, depth: item.z };
      // The visible support edge is the footprint face nearest the room centre.
      if (item.wall === 'north') point.depth += item.depth / 2;
      else if (item.wall === 'south') point.depth -= item.depth / 2;
      else if (item.wall === 'east') point.x -= item.width / 2;
      else if (item.wall === 'west') point.x += item.width / 2;
      else {
        const dx = l.width / 2 - item.x,
          dz = l.depth / 2 - item.z;
        if (Math.abs(dx) > Math.abs(dz)) point.x += (Math.sign(dx) * item.width) / 2;
        else point.depth += (Math.sign(dz) * item.depth) / 2;
      }
      const projected = camera.projection.projectPoint(point, item.elevation);
      view.zIndex = -projected.depth;
      view.visible = projected.depth > 1;
      // Each cutout stays on a fixed furniture face while the user turns.
      // Physical footprint dimensions determine its projected width.
      const alongZ =
        item.wall === 'west' ||
        item.wall === 'east' ||
        (!item.wall && Math.abs(l.width / 2 - item.x) > Math.abs(l.depth / 2 - item.z));
      const width = alongZ ? item.depth : item.width;
      this.faces.set(item.id, { point, alongZ, width });
      this.surface(
        view,
        camera,
        (u, v) => [
          alongZ
            ? { x: point.x, depth: point.depth + (u - item.pivot[0]) * width }
            : { x: point.x + (u - item.pivot[0]) * width, depth: point.depth },
          item.elevation + (item.pivot[1] - v) * item.height,
        ],
        8,
        4,
      );
    }
  }
}
