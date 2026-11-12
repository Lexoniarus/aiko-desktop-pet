import type { RoomLayout, RoomPoint } from './RoomLayout';
import { roomPresentation } from './RoomPresentation.ts';
import { approachScale } from './RoomPlayerFraming.ts';

const quarterTurn = Math.PI / 2;
const flatPanelSpan = 0.86;

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
  private wallCoordinates(point: RoomPoint) {
    const x = (2 * point.x) / this.layout.width - 1;
    const z = (2 * point.depth) / this.layout.depth - 1;
    if (Math.abs(z) >= Math.abs(x)) {
      return { wall: z <= 0 ? 0 : 2, normal: Math.abs(z), lateral: z <= 0 ? x : -x };
    }
    return { wall: x > 0 ? 1 : -1, normal: Math.abs(x), lateral: x > 0 ? z : -z };
  }
  wallBearing(point: RoomPoint): number {
    return this.wallCoordinates(point).wall * quarterTurn;
  }
  bearing(point: RoomPoint): number {
    const { wall, normal, lateral } = this.wallCoordinates(point);
    const inner = flatPanelSpan * normal;
    const offset = Math.abs(lateral);
    // The middle of each panel is orthogonal. Only the small seam strip
    // stretches to join the neighboring wall continuously.
    const along =
      offset <= inner || normal >= 1
        ? lateral
        : Math.sign(lateral) *
          (inner + ((offset - inner) / (normal - inner)) * (1 - inner));
    return (wall + along / 2) * quarterTurn;
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
  private pointOnPanel(bearing: number, normal: number): RoomPoint {
    const strip = (((bearing / quarterTurn + 0.5) % 4) + 4) % 4;
    const wall = Math.floor(strip);
    const along = 2 * (strip - wall) - 1;
    const inner = flatPanelSpan * normal;
    const offset = Math.abs(along);
    const lateral =
      offset <= inner || normal >= 1
        ? along
        : Math.sign(along) *
          (inner + ((offset - inner) / (1 - inner)) * (normal - inner));
    const x =
      wall === 0 ? lateral : wall === 1 ? normal : wall === 2 ? -lateral : -normal;
    const z =
      wall === 0 ? -normal : wall === 1 ? lateral : wall === 2 ? normal : -lateral;
    return {
      x: ((1 + x) * this.layout.width) / 2,
      depth: ((1 + z) * this.layout.depth) / 2,
    };
  }
  private distance(point: RoomPoint): number {
    return Math.hypot(
      point.x - this.layout.width / 2,
      point.depth - this.layout.depth / 2,
    );
  }
  private floorCloseness(point: RoomPoint): number {
    const { normal } = this.wallCoordinates(point);
    if (normal === 0) return 2;
    const edge = this.distance(point) / normal;
    return ((1 - normal) * edge) / (edge - this.layout.camera_clearance);
  }
  private atPanelMeasure(
    bearing: number,
    target: number,
    measure: (point: RoomPoint) => number,
  ): RoomPoint {
    let near = 0,
      far = 1;
    for (let i = 0; i < 40; i++) {
      const middle = (near + far) / 2;
      if (measure(this.pointOnPanel(bearing, middle)) < target) near = middle;
      else far = middle;
    }
    return this.pointOnPanel(bearing, (near + far) / 2);
  }
  pointAtBearing(bearing: number, distance: number): RoomPoint {
    const edge = this.pointOnPanel(bearing, 1);
    const edgeDistance = this.distance(edge);
    if (distance >= edgeDistance) {
      const centreX = this.layout.width / 2,
        centreZ = this.layout.depth / 2;
      const factor = distance / edgeDistance;
      return {
        x: centreX + (edge.x - centreX) * factor,
        depth: centreZ + (edge.depth - centreZ) * factor,
      };
    }
    return this.atPanelMeasure(bearing, distance, (point) => this.distance(point));
  }
  actorScale(point: RoomPoint): number {
    const { normal } = this.wallCoordinates(point);
    const limit =
      this.layout.camera_clearance /
      Math.hypot(this.layout.width / 2, this.layout.depth / 2);
    const progress = (value: number) =>
      Math.max(0, Math.min(1, (1 - value) / (1 - limit)));
    // Keep the usual room size at the normal starting depth. Near/far motion
    // uses the authored approach curve, independent of lateral position.
    const normalSize =
      3.2 +
      1.2 *
        this.floorCloseness({
          x: this.layout.width / 2,
          depth: this.layout.depth / 6,
        });
    return (
      (normalSize * this.fit * approachScale(progress(normal))) /
      approachScale(progress(2 / 3))
    );
  }
  projectPoint(
    point: RoomPoint,
    height = 0,
  ): { x: number; y: number; depth: number; scale: number; groundY: number } {
    const bearing = this.bearing(point);
    const distance = this.distance(point);
    const closeness = Math.max(0, Math.min(1, this.floorCloseness(point)));
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
    return this.atPanelMeasure(
      this.screenBearing(x),
      1 - closeness,
      (point) => 1 - this.floorCloseness(point),
    );
  }
  foodPlacement(x: number, y: number): { point: RoomPoint; height: number } {
    const point = this.atPanelMeasure(
      this.screenBearing(x),
      1 - this.layout.food_line,
      (point) => 1 - this.floorCloseness(point),
    );
    const ground = this.projectPoint(point);
    return { point, height: Math.max(0, Math.min(225, (ground.y - y) / ground.scale)) };
  }
  atDistance(
    x: number,
    y: number,
    previous: RoomPoint,
  ): { point: RoomPoint; height: number } {
    const distance = this.distance(previous);
    const point = this.pointAtBearing(this.screenBearing(x), distance);
    const ground = this.projectPoint(point);
    return { point, height: Math.max(0, Math.min(225, (ground.y - y) / ground.scale)) };
  }
}
