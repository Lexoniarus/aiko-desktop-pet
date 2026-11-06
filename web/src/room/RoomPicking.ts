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
    const placement = this.camera.projection.atDistance(x, y, point);
    return canPlace(this.camera.layout, placement.point) ? placement : undefined;
  }
}
