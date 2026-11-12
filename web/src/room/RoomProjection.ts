import {
  worldPolar,
  worldPoint,
  type RoomLayout,
  type RoomPoint,
} from './RoomLayout.ts';
import { roomPresentation } from './RoomPresentation.ts';

/** Flat wall artwork and one camera-relative floor shared by actors and objects. */
export class RoomProjection {
  readonly designHeight = roomPresentation.designHeight;
  readonly panelWidth = roomPresentation.panelWidth;
  width = 1;
  height = 1;
  readonly layout: RoomLayout;
  private yaw = 0;
  private readonly farDistance: number;
  private readonly farInverse: number;
  private readonly nearInverse: number;
  private horizon = 0;
  private magnification = 1;

  constructor(layout: RoomLayout) {
    this.layout = layout;
    this.farDistance = Math.hypot(layout.width / 2, layout.depth / 2);
    this.farInverse = this.inverseDepth(this.farDistance);
    this.nearInverse = this.inverseDepth(this.nearDistance);
  }

  get nearDistance(): number {
    return this.layout.camera_clearance + this.layout.pet_radius;
  }

  get floorLine(): number {
    return Math.max(0, Math.min(this.height, this.yAt(this.farDistance)));
  }

  get fit(): number {
    return this.magnification;
  }

  get angularScale(): number {
    return roomPresentation.focalLength * this.fit;
  }

  update(
    width: number,
    height: number,
    yaw: number,
    fit = height / this.designHeight,
    horizon = height * roomPresentation.horizon,
  ): void {
    this.width = width;
    this.height = height;
    this.yaw = yaw;
    this.magnification = fit;
    this.horizon = horizon;
  }

  bearing(point: RoomPoint): number {
    return worldPolar(this.layout, point).bearing;
  }

  screenX(bearing: number): number {
    const delta = Math.atan2(
      Math.sin(bearing - this.yaw),
      Math.cos(bearing - this.yaw),
    );
    return this.width / 2 + delta * this.angularScale;
  }

  screenBearing(x: number): number {
    return this.yaw + (x - this.width / 2) / this.angularScale;
  }

  pointAtBearing(bearing: number, distance: number): RoomPoint {
    return worldPoint(this.layout, bearing, distance);
  }

  private inverseDepth(distance: number): number {
    return 1 / Math.max(distance, 1);
  }

  scaleAt(distance: number): number {
    return this.angularScale * this.inverseDepth(distance);
  }

  yAt(distance: number, elevation = 0): number {
    return (
      this.horizon + (this.layout.camera_height - elevation) * this.scaleAt(distance)
    );
  }

  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
    const depth = worldPolar(this.layout, point).distance;
    const scale = this.scaleAt(depth);
    const groundY = this.yAt(depth);
    return {
      x: this.screenX(this.bearing(point)),
      y: groundY - height * scale,
      groundY,
      depth,
      scale,
    };
  }

  projectAiko(point: RoomPoint, callDistance: number, frontalHalfWidth: number) {
    const projected = this.projectPoint(point);
    const maxScale = Math.max(1, this.width - 24) / (2 * frontalHalfWidth);
    const near = this.nearDistance;
    const progress = Math.max(
      0,
      Math.min(1, (near - projected.depth) / (near - callDistance)),
    );
    if (!progress) return { ...projected, scale: Math.min(projected.scale, maxScale) };

    // Keep the frontal silhouette inside a tall viewport and the lower body
    // below its bottom edge. The camera and the physical depth stay fixed.
    const displayDistance = near * (1 - 0.2 * progress);
    const scale = Math.min(this.scaleAt(displayDistance), maxScale);
    const closeScale = Math.min(this.scaleAt(near * 0.8), maxScale);
    const entryY = this.yAt(near);
    const closeY = Math.max(
      entryY,
      this.height + 0.3 * this.layout.pet_height * closeScale,
    );
    const groundY = entryY + (closeY - entryY) * progress;
    return { ...projected, y: groundY, groundY, scale };
  }

  intersectFloor(x: number, y: number, height = 0): RoomPoint | undefined {
    const divisor = (this.layout.camera_height - height) * this.angularScale;
    if (Math.abs(divisor) < 1e-6) return;
    const inverse = (y - this.horizon) / divisor;
    if (inverse < this.farInverse - 1e-9 || inverse > this.nearInverse + 1e-9) return;
    return this.pointAtBearing(this.screenBearing(x), 1 / inverse);
  }

  foodPlacement(x: number, y: number): { point: RoomPoint; height: number } {
    const inverse =
      this.farInverse + (this.nearInverse - this.farInverse) * this.layout.food_line;
    return this.atDepth(x, y, 1 / inverse);
  }

  atDistance(
    x: number,
    y: number,
    previous: RoomPoint,
  ): { point: RoomPoint; height: number } {
    return this.atDepth(x, y, worldPolar(this.layout, previous).distance);
  }

  private atDepth(x: number, y: number, distance: number) {
    const point = this.pointAtBearing(this.screenBearing(x), distance);
    const ground = this.projectPoint(point);
    return { point, height: Math.max(0, Math.min(225, (ground.y - y) / ground.scale)) };
  }
}
