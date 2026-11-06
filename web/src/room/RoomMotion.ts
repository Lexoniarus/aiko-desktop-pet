import type { RoomPoint } from './RoomLayout';
type Point = RoomPoint & { height?: number };
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
        for (let i = 0; i < lengths.length; i++) {
          const length = lengths[i]!;
          if (remaining <= length && length > 0) {
            const a = path[i]!,
              b = path[i + 1]!,
              t = remaining / length;
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
        return result;
      }
      from = to;
    }
    return { ...from.point };
  }
}
