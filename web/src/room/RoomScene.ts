import { Container, Graphics, Mesh, MeshGeometry, Sprite, Texture } from 'pixi.js';
import type { RoomCamera } from './RoomCamera';
import type { FurniturePlacement, RoomLayout, RoomPoint } from './RoomLayout';

/** Static room art shares its ground anchors with Python's occupied footprints. */
export class RoomScene {
  private floor = new Graphics();
  private walls: Array<{ mesh: Mesh<MeshGeometry>; wall: string }> = [];
  private furniture: Array<{ view: Sprite | Mesh<MeshGeometry>; item: FurniturePlacement }> = [];
  private lastVersion = -1;
  constructor(private world: Container, private layout: RoomLayout,
    images: Record<string, HTMLImageElement>) {
    this.floor.zIndex = -10000;
    world.addChild(this.floor);
    for (const [wall, source] of [['north', images.kitchen!], ['east', images.living!],
      ['south', images.kitchen!], ['west', images.living!]] as const) {
      const canvas = document.createElement('canvas');
      canvas.width = 1600; canvas.height = 750;
      canvas.getContext('2d')!.drawImage(source, 0, source.height * .06, source.width, source.height * .83, 0, 0, 1600, 750);
      const mesh = new Mesh({ geometry: new MeshGeometry(), texture: Texture.from(canvas) });
      mesh.zIndex = -9000;
      world.addChild(mesh); this.walls.push({mesh, wall});
    }
    for (const item of layout.furniture) {
      const [x, y, w, h] = item.crop;
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d')!.drawImage(images[item.asset]!, x, y, w, h, 0, 0, w, h);
      const texture = Texture.from(canvas);
      const view = item.id === 'door' || item.id === 'shelf'
        ? new Mesh({geometry: new MeshGeometry(), texture}) : new Sprite(texture);
      if (view instanceof Sprite) view.anchor.set(...item.pivot);
      view.eventMode = 'none'; world.addChild(view); this.furniture.push({view, item});
    }
  }
  private wallPoint(wall: string, along: number, height: number): [RoomPoint, number] {
    const l = this.layout;
    if (wall === 'north') return [{x: along, depth: 0}, height];
    if (wall === 'east') return [{x: l.width, depth: along}, height];
    if (wall === 'south') return [{x: l.width - along, depth: l.depth}, height];
    return [{x: 0, depth: l.depth - along}, height];
  }
  private surface(mesh: Mesh<MeshGeometry>, camera: RoomCamera,
    point: (u: number, v: number) => [RoomPoint, number], columns: number, rows: number): void {
    const positions: number[] = [], uvs: number[] = [], indices: number[] = [];
    for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
      const corners = [[x / columns, y / rows], [(x + 1) / columns, y / rows],
        [(x + 1) / columns, (y + 1) / rows], [x / columns, (y + 1) / rows]] as const;
      const projected = corners.map(([u, v]) => camera.projection.projectPoint(...point(u, v)));
      if (projected.some(p => p.depth < 1)) continue;
      const offset = positions.length / 2;
      for (let i = 0; i < 4; i++) {
        positions.push(projected[i]!.x, projected[i]!.y); uvs.push(...corners[i]!);
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
    const l = this.layout;
    this.floor.clear();
    const cell = 50;
    for (let z = 0; z < l.depth; z += cell) for (let x = 0; x < l.width; x += cell) {
      const points = [[x,z], [x+cell,z], [x+cell,z+cell], [x,z+cell]]
        .map(([px,pz]) => camera.projection.projectPoint({x: px!, depth: pz!}));
      if (points.some(p => p.depth < 1)) continue;
      this.floor.poly(points.flatMap(p => [p.x,p.y])).fill((x/cell+z/cell)%2 ? 0xd4bb98 : 0xdbc4a5);
    }
    for (const {mesh, wall} of this.walls) {
      const length = wall === 'north' || wall === 'south' ? l.width : l.depth;
      this.surface(mesh, camera, (u,v) => this.wallPoint(wall, u*length, (1-v)*l.wall_height), 32, 8);
    }
    for (const {view, item} of this.furniture) {
      const point = {x: item.x, depth: item.z};
      // The visible support edge is the footprint face nearest the room centre.
      if (item.wall === 'north') point.depth += item.depth / 2;
      else if (item.wall === 'south') point.depth -= item.depth / 2;
      else if (item.wall === 'east') point.x -= item.width / 2;
      else if (item.wall === 'west') point.x += item.width / 2;
      else {
        const dx = l.width/2-item.x, dz = l.depth/2-item.z;
        if (Math.abs(dx) > Math.abs(dz)) point.x += Math.sign(dx)*item.width/2;
        else point.depth += Math.sign(dz)*item.depth/2;
      }
      const projected = camera.projection.projectPoint(point, item.elevation);
      view.zIndex = -projected.depth;
      view.visible = projected.depth > 1;
      if (view instanceof Sprite) {
        view.position.set(projected.x, projected.y);
        view.scale.set(item.height / view.texture.height * projected.scale);
      } else {
        const width = item.height * view.texture.width / view.texture.height;
        this.surface(view, camera, (u,v) => [
          item.wall === 'west' || item.wall === 'east'
            ? {x: point.x, depth: point.depth + (u-.5)*width}
            : {x: point.x + (u-.5)*width, depth: point.depth},
          item.elevation+(1-v)*item.height,
        ], 8, 8);
      }
    }
  }
}
