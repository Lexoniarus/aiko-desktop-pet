import type { PetScreenBounds } from './AikoView';
import type { RoomCamera } from './RoomCamera';
import { canPlace, type RoomPoint } from './RoomLayout.ts';

export function hitsNearHandover(
  x: number,
  y: number,
  pet: PetScreenBounds,
  width: number,
  height: number,
): boolean {
  return (
    x >= Math.max(0, pet.x + pet.width * 0.2) &&
    x <= Math.min(width, pet.x + pet.width * 0.8) &&
    y >= Math.max(0, pet.y + pet.height * 0.55) &&
    y <= Math.min(height, pet.y + pet.height * 0.84)
  );
}

/** Preview only. The Python owner independently validates every committed drop. */
export class RoomPicking {
  private readonly camera: RoomCamera;

  constructor(camera: RoomCamera) {
    this.camera = camera;
  }

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
