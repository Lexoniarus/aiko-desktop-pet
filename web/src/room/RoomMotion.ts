import {
  worldPoint,
  worldPolar,
  type RoomLayout,
  type RoomPoint,
} from './RoomLayout.ts';
import type { RoomWalk, RoomWalkClip } from './RoomWalkPresentation.ts';

type Point = RoomPoint & { height?: number };
type Gait = {
  time: number;
  distance: number;
  step_length: number;
  step_duration: number;
};
type MotionSample = { point: Point; walk?: RoomWalk };
type Segment = {
  length: number;
  at: (fraction: number) => RoomPoint;
  clip?: RoomWalkClip;
};
type Snapshot = { point: Point; time: number; legs: Segment[]; gait?: Gait };

const epsilon = 1e-8;
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

function segment(start: RoomPoint, end: RoomPoint, layout?: RoomLayout): Segment {
  if (layout) {
    const first = worldPolar(layout, start);
    const last = worldPolar(layout, end);
    const bearing = last.bearing - first.bearing;
    const turn = Math.atan2(Math.sin(bearing), Math.cos(bearing));
    const radial = last.distance - first.distance;
    if (Math.abs(turn) < epsilon) {
      return {
        length: Math.abs(radial),
        at: (t) =>
          worldPoint(layout, first.bearing, mix(first.distance, last.distance, t)),
        clip: radial < 0 ? 'room-walk-toward' : 'room-walk-away',
      };
    }
    if (Math.abs(radial) < epsilon) {
      return {
        length: Math.abs(turn * first.distance),
        at: (t) => worldPoint(layout, first.bearing + turn * t, first.distance),
        clip: turn > 0 ? 'body-step-right-profil' : 'body-step-left-profil',
      };
    }
  }
  return {
    length: Math.hypot(end.x - start.x, end.depth - start.depth),
    at: (t) => ({ x: mix(start.x, end.x, t), depth: mix(start.depth, end.depth, t) }),
  };
}

/** Follow the admitted arcs and rays for Aiko. Objects use linear interpolation. */
export class RoomMotion {
  private samples: Snapshot[] = [];
  private readonly layout?: RoomLayout;

  constructor(layout?: RoomLayout) {
    this.layout = layout;
  }

  receive(
    point: Point,
    now = performance.now(),
    travelled: RoomPoint[] = [],
    gait?: Gait,
  ): void {
    const last = this.samples.at(-1);
    if (last && (now <= last.time || (gait && gait.time === last.gait?.time))) return;
    const path = last
      ? [
          last.point,
          ...(gait && gait.distance === last.gait?.distance ? [] : travelled),
          point,
        ]
      : [];
    const legs = path
      .slice(1)
      .map((end, index) => segment(path[index]!, end, this.layout))
      .filter((leg) => leg.length > epsilon);
    this.samples.push({ point: { ...point }, time: now, legs, gait });
    while (this.samples.length > 2 && this.samples[1]!.time < now - 1000)
      this.samples.shift();
  }

  position(now = performance.now()): Point | undefined {
    return this.sample(now)?.point;
  }

  sample(now = performance.now()): MotionSample | undefined {
    if (!this.samples.length) return;
    const time = now - 100;
    let from = this.samples[0]!;
    for (const to of this.samples.slice(1)) {
      if (to.time > time) {
        if (time < from.time) return { point: from.point };
        const fraction = (time - from.time) / (to.time - from.time);
        const length = to.legs.reduce((sum, leg) => sum + leg.length, 0);
        const gait = to.gait;
        const simulated = gait && from.gait ? gait.time - from.gait.time : 0;
        const speed = gait ? gait.step_length / gait.step_duration : 0;
        // Arrival can use only part of the last simulation tick. Stop at the
        // endpoint as soon as the distance budget is exhausted.
        const budget = Math.max(length, simulated * speed);
        const travelled = fraction * budget;
        let remaining = travelled;
        let point: Point = { ...to.point };
        let walk: RoomWalk | undefined;
        for (const leg of to.legs) {
          if (remaining < leg.length) {
            point = leg.at(remaining / leg.length);
            if (leg.clip && gait) {
              walk = {
                clip: leg.clip,
                distance: (from.gait?.distance ?? gait.distance - length) + travelled,
                stepLength: gait.step_length,
                stepDuration: gait.step_duration,
              };
            }
            break;
          }
          remaining -= leg.length;
        }
        if (from.point.height !== undefined && to.point.height !== undefined)
          point.height = mix(from.point.height, to.point.height, fraction);
        return { point, walk };
      }
      from = to;
    }
    return { point: { ...from.point } };
  }
}
