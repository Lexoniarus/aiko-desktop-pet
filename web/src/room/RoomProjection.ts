import type { RoomLayout, RoomPoint } from './RoomLayout';

/** Flat panorama over the existing floor grid; never a perspective camera. */
export class RoomProjection {
  readonly designHeight = 900;
  readonly panelWidth = 1800;
  readonly floorBack = 690;
  readonly floorFront = 860;
  width = 1;
  height = 1;
  private yaw = 0;
  constructor(readonly layout: RoomLayout) {}
  get fit(): number {
    return this.height / this.designHeight;
  }
  get angularScale(): number {
    return (this.panelWidth * 2 * this.fit) / Math.PI;
  }
  update(width: number, height: number, yaw: number): void {
    this.width = width;
    this.height = height;
    this.yaw = yaw;
  }
  bearing(point: RoomPoint): number {
    return Math.atan2(
      point.x - this.layout.width / 2,
      this.layout.depth / 2 - point.depth,
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
  private edgeDistance(bearing: number): number {
    return Math.min(
      this.layout.width / (2 * Math.max(1e-9, Math.abs(Math.sin(bearing)))),
      this.layout.depth / (2 * Math.max(1e-9, Math.abs(Math.cos(bearing)))),
    );
  }
  private position(bearing: number, distance: number): RoomPoint {
    return {
      x: this.layout.width / 2 + Math.sin(bearing) * distance,
      depth: this.layout.depth / 2 - Math.cos(bearing) * distance,
    };
  }
  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number } {
    const bearing = this.bearing(point);
    const distance = Math.hypot(
      point.x - this.layout.width / 2,
      point.depth - this.layout.depth / 2,
    );
    const edge = this.edgeDistance(bearing);
    const closeness = Math.max(
      0,
      Math.min(1, (edge - distance) / (edge - this.layout.camera_clearance)),
    );
    const scale = (3.2 + 1.2 * closeness) * this.fit;
    return {
      x: this.screenX(bearing),
      y:
        (this.floorBack + (this.floorFront - this.floorBack) * closeness) * this.fit -
        height * scale,
      depth: distance,
      scale,
    };
  }
  intersectFloor(x: number, y: number, height = 0): RoomPoint | undefined {
    const divisor = this.floorFront - this.floorBack - height * 1.2;
    if (Math.abs(divisor) < 1e-6) return;
    const closeness = (y / this.fit - this.floorBack + height * 3.2) / divisor;
    if (closeness < 0 || closeness > 1) return;
    const bearing = this.screenBearing(x),
      edge = this.edgeDistance(bearing);
    return this.position(
      bearing,
      edge - closeness * (edge - this.layout.camera_clearance),
    );
  }
  atDistance(
    x: number,
    y: number,
    previous: RoomPoint,
  ): { point: RoomPoint; height: number } {
    const distance = Math.hypot(
      previous.x - this.layout.width / 2,
      previous.depth - this.layout.depth / 2,
    );
    const point = this.position(this.screenBearing(x), distance);
    const ground = this.projectPoint(point);
    return { point, height: Math.max(0, Math.min(225, (ground.y - y) / ground.scale)) };
  }
}
