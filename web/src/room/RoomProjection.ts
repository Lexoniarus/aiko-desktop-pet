import {
  worldPolar,
  worldPoint,
  type RoomLayout,
  type RoomPoint,
} from './RoomLayout.ts';
import { closeCrop, depthReferenceHeight, RoomDepthCurve } from './RoomDepthCurve.ts';
import { roomPresentation } from './RoomPresentation.ts';

const referenceFit = depthReferenceHeight / roomPresentation.designHeight;
const referenceHorizon = depthReferenceHeight * roomPresentation.horizon;

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
  private readonly calibratedCallDistance?: number;
  private readonly depthCurve?: RoomDepthCurve;
  private horizon = 0;
  private magnification = 1;

  constructor(layout: RoomLayout, calibratedCallDistance?: number) {
    this.layout = layout;
    this.calibratedCallDistance = calibratedCallDistance;
    this.farDistance = Math.hypot(layout.width / 2, layout.depth / 2);
    this.farInverse = this.inverseDepth(this.farDistance);
    this.nearInverse = this.inverseDepth(this.nearDistance);
    if (calibratedCallDistance !== undefined) {
      const floorY =
        referenceHorizon +
        layout.camera_height *
          roomPresentation.focalLength *
          referenceFit *
          this.farInverse;
      this.depthCurve = new RoomDepthCurve(
        this.farDistance,
        this.nearDistance + 1,
        calibratedCallDistance,
        floorY,
      );
    }
  }

  get nearDistance(): number {
    return this.layout.camera_clearance + this.layout.pet_radius;
  }

  get floorLine(): number {
    return Math.max(0, Math.min(this.height, this.floorBounds.top));
  }

  /** The floor raster and the projected radius use the same camera transform. */
  get floorBounds(): { top: number; height: number } {
    const top = this.yAt(this.farDistance);
    const height = this.depthCurve
      ? (depthReferenceHeight - this.depthCurve.floorY) * (this.fit / referenceFit)
      : this.height - top;
    return { top, height };
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
    return this.groundAt(distance).scale;
  }

  yAt(distance: number, elevation = 0): number {
    const { groundY, scale } = this.groundAt(distance);
    return groundY - elevation * scale;
  }

  private groundAt(distance: number): { groundY: number; scale: number } {
    if (this.depthCurve && Number.isFinite(distance)) {
      const frame = this.depthCurve.at(distance);
      const fit = this.fit / referenceFit;
      return {
        groundY: this.horizon + (frame.groundY - referenceHorizon) * fit,
        scale: (frame.spriteHeight / this.layout.pet_height) * fit,
      };
    }
    const scale = this.angularScale * this.inverseDepth(distance);
    return { groundY: this.horizon + this.layout.camera_height * scale, scale };
  }

  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
    const { distance: depth, bearing } = worldPolar(this.layout, point);
    const { scale, groundY } = this.groundAt(depth);
    return {
      x: this.screenX(bearing),
      y: groundY - height * scale,
      groundY,
      depth,
      scale,
    };
  }

  projectAiko(point: RoomPoint, callDistance: number, frontalHalfWidth: number) {
    const projected = this.projectPoint(point);
    const maxScale = Math.max(1, this.width - 24) / (2 * frontalHalfWidth);
    if (this.calibratedCallDistance !== undefined) {
      const front = this.nearDistance + 1;
      const close = this.calibratedCallDistance;
      const progress = Math.max(
        0,
        Math.min(1, (front - projected.depth) / (front - close)),
      );
      const scale = Math.min(projected.scale, maxScale);
      const closeScale = this.scaleAt(close);
      // Keep the shared floor contact through the ordinary walk. Only the
      // cropped close pose needs a vertical correction for narrow screens.
      const missingHeight =
        (closeScale - Math.min(closeScale, maxScale)) * this.layout.pet_height;
      const groundY =
        projected.groundY -
        closeCrop * missingHeight * progress ** 2 * (3 - 2 * progress);
      return { ...projected, groundY, y: groundY, scale };
    }
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
    const bearing = this.screenBearing(x);
    if (this.depthCurve) {
      return this.intersectCalibratedFloor(bearing, y, height);
    }
    const divisor = (this.layout.camera_height - height) * this.angularScale;
    if (Math.abs(divisor) < 1e-6) return;
    const inverse = (y - this.horizon) / divisor;
    if (inverse < this.farInverse - 1e-9 || inverse > this.nearInverse + 1e-9) return;
    return this.pointAtBearing(bearing, 1 / inverse);
  }

  private intersectCalibratedFloor(bearing: number, y: number, elevation: number) {
    let near = this.nearDistance;
    let far = Math.min(
      this.layout.width / (2 * Math.abs(Math.sin(bearing))),
      this.layout.depth / (2 * Math.abs(Math.cos(bearing))),
    );
    const screenY = (radius: number) => this.yAt(radius, elevation);
    const nearY = screenY(near),
      farY = screenY(far);
    if (
      Math.abs(nearY - farY) < 1e-8 ||
      y < Math.min(nearY, farY) - 1e-8 ||
      y > Math.max(nearY, farY) + 1e-8
    ) {
      return undefined;
    }
    for (let i = 0; i < 42; i++) {
      const mid = (near + far) / 2;
      if (screenY(mid) > y === nearY > farY) near = mid;
      else far = mid;
    }
    return this.pointAtBearing(bearing, (near + far) / 2);
  }

  get floorLimit(): number {
    return this.yAt(this.nearDistance);
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
