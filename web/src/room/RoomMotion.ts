import type { RoomPoint } from './RoomLayout';
type Point = RoomPoint & { height?: number };
type MotionSample = { point: Point; heading?: number };
/** Interpolate along admitted route segments, never across a furniture corner. */
export class RoomMotion {
  private samples: Array<{ point: Point; time: number; path: RoomPoint[] }> = [];
  receive(point: Point, now = performance.now(), travelled: RoomPoint[] = []): void {
    const last = this.samples.at(-1);
    if (last && now <= last.time) return;
    this.samples.push({
      point: { ...point },
      time: now,
      path: travelled.map((p) => ({ ...p })),
    });
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
      if (to.time >= time) {
        const fraction = Math.max(
          0,
          Math.min(1, (time - from.time) / (to.time - from.time)),
        );
        const path = [from.point, ...to.path, to.point];
        const lengths = path
          .slice(1)
          .map((p, i) => Math.hypot(p.x - path[i]!.x, p.depth - path[i]!.depth));
        let remaining = lengths.reduce((a, b) => a + b, 0) * fraction;
        let point: RoomPoint = to.point;
        let heading: number | undefined;
        for (let i = 0; i < lengths.length; i++) {
          const length = lengths[i]!;
          if (length === 0) continue;
          const a = path[i]!,
            b = path[i + 1]!;
          heading = Math.atan2(b.x - a.x, a.depth - b.depth);
          if (remaining < length) {
            const t = remaining / length;
            point = {
              x: a.x + (b.x - a.x) * t,
              depth: a.depth + (b.depth - a.depth) * t,
            };
            break;
          }
          remaining -= length;
        }
        const result: Point = { ...point };
        if (from.point.height !== undefined && to.point.height !== undefined)
          result.height =
            from.point.height + (to.point.height - from.point.height) * fraction;
        return { point: result, heading };
      }
      from = to;
    }
    return { point: { ...from.point } };
  }
}
