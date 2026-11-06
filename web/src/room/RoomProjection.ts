import { mat4, vec3, vec4 } from 'gl-matrix';
import type { RoomLayout, RoomPoint } from './RoomLayout';

export class RoomProjection {
  readonly matrix = mat4.create();
  private inverse = mat4.create();
  private view = mat4.create();
  width = 1;
  height = 1;
  private focal = 1;
  readonly layout: RoomLayout;
  constructor(layout: RoomLayout) {
    this.layout = layout;
  }
  update(width: number, height: number, yaw: number): void {
    this.width = width;
    this.height = height;
    const pitch = (8 * Math.PI) / 180;
    const eye = vec3.fromValues(
      this.layout.width / 2,
      this.layout.camera_height,
      this.layout.depth / 2,
    );
    const target = vec3.fromValues(
      eye[0]! + Math.sin(yaw) * Math.cos(pitch),
      eye[1]! - Math.sin(pitch),
      eye[2]! - Math.cos(yaw) * Math.cos(pitch),
    );
    mat4.lookAt(this.view, eye, target, [0, 1, 0]);
    const perspective = mat4.perspective(
      mat4.create(),
      (55 * Math.PI) / 180,
      width / height,
      1,
      2500,
    );
    mat4.multiply(this.matrix, perspective, this.view);
    mat4.invert(this.inverse, this.matrix);
    this.focal = height / (2 * Math.tan((55 * Math.PI) / 360));
  }
  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number } {
    const clip = vec4.transformMat4(
      vec4.create(),
      [point.x, height, point.depth, 1],
      this.matrix,
    );
    const depth = clip[3]!;
    return {
      x: ((clip[0]! / depth + 1) * this.width) / 2,
      y: ((1 - clip[1]! / depth) * this.height) / 2,
      depth,
      scale: this.focal / Math.max(1, depth),
    };
  }
  screenRay(x: number, y: number): { origin: vec3; direction: vec3 } {
    const sample = (z: number): vec3 => {
      const p = vec4.transformMat4(
        vec4.create(),
        [(2 * x) / this.width - 1, 1 - (2 * y) / this.height, z, 1],
        this.inverse,
      );
      return vec3.fromValues(p[0]! / p[3]!, p[1]! / p[3]!, p[2]! / p[3]!);
    };
    const origin = sample(-1);
    return {
      origin,
      direction: vec3.normalize(
        vec3.create(),
        vec3.subtract(vec3.create(), sample(1), origin),
      ),
    };
  }
  intersectFloor(x: number, y: number, height = 0): RoomPoint | undefined {
    const ray = this.screenRay(x, y);
    if (ray.direction[1]! >= -0.0001) return;
    const t = (height - ray.origin[1]!) / ray.direction[1]!;
    if (t < 0) return;
    return {
      x: ray.origin[0]! + t * ray.direction[0]!,
      depth: ray.origin[2]! + t * ray.direction[2]!,
    };
  }
  intersectWall(
    x: number,
    y: number,
  ): { wall: string; along: number; height: number } | undefined {
    const ray = this.screenRay(x, y),
      results: Array<{ wall: string; along: number; height: number; t: number }> = [];
    for (const [wall, axis, plane, length] of [
      ['north', 2, 0, this.layout.width],
      ['east', 0, this.layout.width, this.layout.depth],
      ['south', 2, this.layout.depth, this.layout.width],
      ['west', 0, 0, this.layout.depth],
    ] as const) {
      const t = (plane - ray.origin[axis]!) / ray.direction[axis]!;
      const along =
        ray.origin[axis === 0 ? 2 : 0]! + t * ray.direction[axis === 0 ? 2 : 0]!;
      const height = ray.origin[1]! + t * ray.direction[1]!;
      if (
        t > 0 &&
        along >= 0 &&
        along <= length &&
        height >= 0 &&
        height <= this.layout.wall_height
      )
        results.push({ wall, along, height, t });
    }
    return results.sort((a, b) => a.t - b.t)[0];
  }
}
