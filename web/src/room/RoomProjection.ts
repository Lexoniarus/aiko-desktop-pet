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
  readonly floorBack = roomPresentation.floorBack;
  readonly floorFront = roomPresentation.floorFront;
  width = 1;
  height = 1;
  readonly layout: RoomLayout;
  private yaw = 0;
  private readonly farInverse: number;
  private readonly nearInverse: number;
  private readonly groundScale: number;
  private readonly horizon: number;
  private readonly spriteScale: number;

  constructor(layout: RoomLayout) {
    this.layout = layout;
    // Calibrate the perspective to the shallow floor strip and the original
    // character size in the default position, 100 units from the north wall.
    this.farInverse = this.inverseDepth(Math.hypot(layout.width / 2, layout.depth / 2));
    this.nearInverse = this.inverseDepth(layout.camera_clearance + layout.pet_radius);
    this.groundScale =
      (this.floorFront - this.floorBack) / (this.nearInverse - this.farInverse);
    this.horizon = this.floorBack - this.groundScale * this.farInverse;
    const referenceDistance = layout.depth / 3;
    const referenceScale =
      3.2 +
      (1.2 * (layout.depth / 2 - referenceDistance)) /
        (layout.depth / 2 - layout.camera_clearance);
    this.spriteScale = referenceScale / this.inverseDepth(referenceDistance);
  }

  get fit(): number {
    return this.height / this.designHeight;
  }

  get angularScale(): number {
    return (this.panelWidth * 2 * this.fit) / Math.PI;
  }

  profileStepLength(stepLength: number): number {
    // Match the profile artwork's stride to its size on the panorama.
    return (stepLength * this.spriteScale * Math.PI) / (this.panelWidth * 2);
  }

  update(width: number, height: number, yaw: number): void {
    this.width = width;
    this.height = height;
    this.yaw = yaw;
  }

  bearing(point: RoomPoint): number {
    // Normalise the rectangular floor to align its corners with the four
    // equally wide panels. Every ray keeps the same screen x at all depths.
    return Math.atan2(
      (2 * point.x) / this.layout.width - 1,
      1 - (2 * point.depth) / this.layout.depth,
    );
  }

  screenX(bearing: number): number {
    const delta = Math.atan2(
      Math.sin(bearing - this.yaw),
      Math.cos(bearing - this.yaw),
    );
    return this.width / 2 + delta * this.angularScale;
  }

  private screenBearing(x: number): number {
    return this.yaw + (x - this.width / 2) / this.angularScale;
  }

  pointAtBearing(bearing: number, distance: number): RoomPoint {
    const angle = Math.atan2(
      this.layout.width * Math.sin(bearing),
      this.layout.depth * Math.cos(bearing),
    );
    return worldPoint(this.layout, angle, distance);
  }

  private inverseDepth(distance: number): number {
    return 1 / Math.max(distance, 1);
  }

  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
    const depth = worldPolar(this.layout, point).distance;
    const inverse = this.inverseDepth(depth);
    const scale = this.spriteScale * inverse * this.fit;
    const groundY = (this.horizon + this.groundScale * inverse) * this.fit;
    return {
      x: this.screenX(this.bearing(point)),
      y: groundY - height * scale,
      groundY,
      depth,
      scale,
    };
  }

  intersectFloor(x: number, y: number, height = 0): RoomPoint | undefined {
    const divisor = this.groundScale - height * this.spriteScale;
    if (Math.abs(divisor) < 1e-6) return;
    const inverse = (y / this.fit - this.horizon) / divisor;
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
