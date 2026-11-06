import type { RoomLayout, RoomPoint } from './RoomLayout';
import { roomPresentation } from './RoomPresentation.ts';

/** Flat panorama over the existing floor grid; never a perspective camera. */
export class RoomProjection {
  readonly designHeight = roomPresentation.designHeight;
  readonly panelWidth = roomPresentation.panelWidth;
  readonly floorBack = roomPresentation.floorBack;
  readonly floorFront = roomPresentation.floorFront;
  width = 1;
  height = 1;
  private yaw = 0;
  readonly layout: RoomLayout;
  constructor(layout: RoomLayout) {
    this.layout = layout;
  }
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
    const dx = point.x - this.layout.width / 2,
      dz = point.depth - this.layout.depth / 2,
      x = Math.abs(dx) / (this.layout.width / 2),
      z = Math.abs(dz) / (this.layout.depth / 2);
    if (x === 0 && z === 0) return 0;
    // Each wall is a linear strip. A radial angular projection put the room's
    // corners inside the wrong panels and changed the apparent furniture gaps.
    if (z >= x) {
      const along = (this.layout.width / 2 + dx / z) / this.layout.width;
      return ((dz < 0 ? along - 0.5 : 2.5 - along) * Math.PI) / 2;
    }
    const along = (this.layout.depth / 2 + dz / x) / this.layout.depth;
    return ((dx > 0 ? along + 0.5 : 3.5 - along) * Math.PI) / 2;
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
  private boundary(bearing: number): RoomPoint {
    const strip = (((bearing / (Math.PI / 2) + 0.5) % 4) + 4) % 4;
    const wall = Math.floor(strip),
      along = strip - wall;
    if (wall === 0) return { x: along * this.layout.width, depth: 0 };
    if (wall === 1) return { x: this.layout.width, depth: along * this.layout.depth };
    if (wall === 2)
      return { x: (1 - along) * this.layout.width, depth: this.layout.depth };
    return { x: 0, depth: (1 - along) * this.layout.depth };
  }
  private edgeDistance(bearing: number): number {
    const edge = this.boundary(bearing);
    return Math.hypot(
      edge.x - this.layout.width / 2,
      edge.depth - this.layout.depth / 2,
    );
  }
  pointAtBearing(bearing: number, distance: number): RoomPoint {
    const edge = this.boundary(bearing),
      ratio = distance / this.edgeDistance(bearing);
    return {
      x: this.layout.width / 2 + (edge.x - this.layout.width / 2) * ratio,
      depth: this.layout.depth / 2 + (edge.depth - this.layout.depth / 2) * ratio,
    };
  }
  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
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
    const groundY =
      (this.floorBack + (this.floorFront - this.floorBack) * closeness) * this.fit;
    return {
      x: this.screenX(bearing),
      y: groundY - height * scale,
      groundY,
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
    return this.pointAtBearing(
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
    const point = this.pointAtBearing(this.screenBearing(x), distance);
    const ground = this.projectPoint(point);
    return { point, height: Math.max(0, Math.min(225, (ground.y - y) / ground.scale)) };
  }
}
