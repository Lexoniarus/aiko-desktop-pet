import { delta, wrap } from './RoomProjection.ts';

type Point = { x: number; depth: number; height?: number };

/** Display interpolation only. Python remains the sole movement owner. */
export class RoomMotion {
  private samples: Array<{ point: Point; time: number }> = [];
  receive(point: Point, now = performance.now()): void {
    const last = this.samples.at(-1);
    if (last && now <= last.time) return;
    this.samples.push({ point: { ...point }, time: now });
    // Keep a short snapshot buffer. Repeated/closely spaced RPC replies no
    // longer restart an easing ramp and change speed several times per step.
    while (this.samples.length > 2 && this.samples[1]!.time < now - 1000)
      this.samples.shift();
  }
  position(now = performance.now()): Point | undefined {
    if (!this.samples.length) return;
    const time = now - 100;
    let from = this.samples[0]!;
    for (const to of this.samples.slice(1)) {
      if (to.time >= time) {
        const fraction = Math.min(
          1,
          Math.max(0, (time - from.time) / (to.time - from.time)),
        );
        const point: Point = {
          x: wrap(from.point.x + delta(from.point.x, to.point.x) * fraction),
          depth: from.point.depth + (to.point.depth - from.point.depth) * fraction,
        };
        if (from.point.height !== undefined && to.point.height !== undefined)
          point.height =
            from.point.height + (to.point.height - from.point.height) * fraction;
        return point;
      }
      from = to;
    }
    return { ...from.point };
  }
}
