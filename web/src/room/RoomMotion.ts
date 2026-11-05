import { delta, wrap } from './RoomProjection';

type Point = { x: number; depth: number };

/** Display interpolation only. Python remains the sole movement owner. */
export class RoomMotion {
  private from?: Point;
  private to?: Point;
  private received = 0;
  private duration = 250;
  receive(point: Point, now = performance.now()): void {
    if (this.to?.x === point.x && this.to.depth === point.depth) return;
    const current = this.position(now);
    this.from = current ?? { ...point };
    this.to = { ...point };
    this.duration = Math.min(500, Math.max(100, now - this.received || 250));
    this.received = now;
  }
  position(now = performance.now()): Point | undefined {
    if (!this.from || !this.to) return;
    const fraction = Math.min(1, Math.max(0, (now - this.received) / this.duration));
    return {
      x: wrap(this.from.x + delta(this.from.x, this.to.x) * fraction),
      depth: this.from.depth + (this.to.depth - this.from.depth) * fraction,
    };
  }
}
