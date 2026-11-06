import type { RoomCamera } from './RoomCamera';
import { canPlace, type RoomPoint } from './RoomLayout';

/** Preview only. The Python owner independently validates every committed drop. */
export class RoomPicking {
  constructor(private camera: RoomCamera) {}
  resolveDrop(x: number, y: number, height = 0): RoomPoint | undefined {
    const point = this.camera.projection.intersectFloor(x, y, height);
    return point && canPlace(this.camera.layout, point) ? point : undefined;
  }
  atDepth(
    x: number,
    y: number,
    point: RoomPoint,
  ): { point: RoomPoint; height: number } | undefined {
    const ray = this.camera.projection.screenRay(x, y);
    // Vertical drag plane through the previous support point, facing the camera.
    const nx = Math.sin(this.camera.yaw),
      nz = -Math.cos(this.camera.yaw);
    const divisor = ray.direction[0]! * nx + ray.direction[2]! * nz;
    if (Math.abs(divisor) < 1e-6) return;
    const t =
      ((point.x - ray.origin[0]!) * nx + (point.depth - ray.origin[2]!) * nz) / divisor;
    const result = {
      x: ray.origin[0]! + t * ray.direction[0]!,
      depth: ray.origin[2]! + t * ray.direction[2]!,
    };
    if (t <= 0 || !canPlace(this.camera.layout, result)) return;
    return {
      point: result,
      height: Math.max(0, Math.min(225, ray.origin[1]! + t * ray.direction[1]!)),
    };
  }
}
