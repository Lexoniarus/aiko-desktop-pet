import {
  worldPolar,
  worldPoint,
  type RoomLayout,
  type RoomPoint,
} from './RoomLayout.ts';
import { floorCurve, northDepth, northWallBlend } from './RoomDepthCurve.ts';
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
  private readonly calibratedCallDistance?: number;
  private horizon = 0;
  private magnification = 1;

  constructor(layout: RoomLayout, calibratedCallDistance?: number) {
    this.layout = layout;
    this.calibratedCallDistance = calibratedCallDistance;
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

  private blendNorth(
    radius: number,
    bearing: number,
    radial: {
      groundY: number;
      scale: number;
    },
    maxScale = Infinity,
  ) {
    if (this.calibratedCallDistance === undefined) return radial;
    const weight = northWallBlend(bearing);
    if (weight === 0) return radial;
    const north = northDepth({
      radius,
      bearing,
      wallAxis: this.layout.depth / 2,
      frontRadius: this.nearDistance + 1,
      closeRadius: this.calibratedCallDistance,
      wallLine: this.floorLine,
      viewportHeight: this.height,
      petHeight: this.layout.pet_height,
      maxScale,
    });
    return {
      groundY: radial.groundY + (north.groundY - radial.groundY) * weight,
      scale: radial.scale + (north.scale - radial.scale) * weight,
    };
  }

  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
    const { distance: depth, bearing } = worldPolar(this.layout, point);
    const { scale, groundY } = this.blendNorth(depth, bearing, {
      scale: this.scaleAt(depth),
      groundY: this.yAt(depth),
    });
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
      const radius = projected.depth;
      const bearing = this.bearing(point);
      const radial = this.calibratedRadialAiko(radius, callDistance, maxScale);
      const { groundY, scale } = this.blendNorth(radius, bearing, radial, maxScale);
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

  private calibratedRadialAiko(radius: number, closeRadius: number, maxScale: number) {
    const front = this.nearDistance + 1;
    const frontScale = this.scaleAt(front);
    if (radius >= front) {
      return {
        groundY: this.yAt(radius),
        scale: Math.min(this.scaleAt(radius), maxScale),
      };
    }
    const span = front - closeRadius;
    const distance = front - Math.max(closeRadius, radius);
    const closeScale = Math.min(this.scaleAt(this.nearDistance * 0.8), maxScale);
    const startScale = Math.min(frontScale, maxScale);
    const scaleSlope = Math.min(
      frontScale / front,
      (3 * (closeScale - startScale)) / span,
    );
    const scale = floorCurve(startScale, closeScale, span, distance, scaleSlope, 0);
    const frontY = this.yAt(front);
    const frontSlope = (this.layout.camera_height * frontScale) / front;
    const closeY = Math.max(
      frontY + (frontSlope * span) / 3,
      this.height + 0.26 * this.layout.pet_height * closeScale,
    );
    const averageSlope = (closeY - frontY) / span;
    const endSlope = Math.min(averageSlope * 1.35, 3 * averageSlope - frontSlope);
    const groundY = floorCurve(
      frontY,
      closeY,
      span,
      distance,
      frontSlope,
      Math.max(0, endSlope),
    );
    return { groundY, scale };
  }

  intersectFloor(x: number, y: number, height = 0): RoomPoint | undefined {
    const bearing = this.screenBearing(x);
    if (
      this.calibratedCallDistance !== undefined &&
      northWallBlend(Math.atan2(Math.sin(bearing), Math.cos(bearing))) > 0
    ) {
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
    const screenY = (radius: number) =>
      this.projectPoint(this.pointAtBearing(bearing, radius), elevation).y;
    const nearY = screenY(near),
      farY = screenY(far);
    if (y < Math.min(nearY, farY) - 1e-8 || y > Math.max(nearY, farY) + 1e-8) {
      return undefined;
    }
    for (let i = 0; i < 42; i++) {
      const mid = (near + far) / 2;
      if (screenY(mid) > y === nearY > farY) near = mid;
      else far = mid;
    }
    return this.pointAtBearing(bearing, (near + far) / 2);
  }

  floorLimitAt(x: number): number {
    return this.projectPoint(
      this.pointAtBearing(this.screenBearing(x), this.nearDistance),
    ).groundY;
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
