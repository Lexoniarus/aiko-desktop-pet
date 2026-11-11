import type { RoomPoint, RoomLayout } from './RoomLayout';
import { RoomProjection } from './RoomProjection.ts';

const panDuration = 320;

export class RoomCamera {
  readonly projection: RoomProjection;
  readonly layout: RoomLayout;
  yaw = 0;
  version = 0;
  following = false;
  private held = false;
  private gameOpen = false;
  private tableGame = false;
  private width = 1;
  private height = 1;
  private pointer?: { id: number; x: number; moved: boolean };
  private velocity = 0;
  private pan?: { from: number; delta: number; started: number };
  private last = performance.now();
  private lastDragAt = -Infinity;
  get blocksTap(): boolean {
    return performance.now() - this.lastDragAt < 350;
  }
  private controller = new AbortController();
  constructor(canvas: HTMLCanvasElement, layout: RoomLayout) {
    this.layout = layout;
    this.projection = new RoomProjection(layout);
    const options = { signal: this.controller.signal };
    canvas.addEventListener(
      'pointerdown',
      (event) => {
        if (!this.held && event.isPrimary)
          this.pointer = { id: event.pointerId, x: event.clientX, moved: false };
        this.velocity = 0;
      },
      options,
    );
    window.addEventListener(
      'pointermove',
      (event) => {
        if (this.held || this.pointer?.id !== event.pointerId) return;
        const dx = event.clientX - this.pointer.x;
        if (!this.pointer.moved && Math.abs(dx) < 6) return;
        this.pointer.moved = true;
        this.lastDragAt = performance.now();
        this.pointer.x = event.clientX;
        this.following = false;
        this.pan = undefined;
        this.velocity = -dx / this.projection.angularScale;
        this.rotateBy(this.velocity);
      },
      options,
    );
    const end = (event: PointerEvent): void => {
      if (this.pointer?.id === event.pointerId) this.pointer = undefined;
    };
    window.addEventListener('pointerup', end, options);
    window.addEventListener(
      'pointercancel',
      (event) => {
        end(event);
        this.velocity = 0;
      },
      options,
    );
  }
  get portraitGame(): boolean {
    return this.gameOpen && !this.tableGame && this.height > this.width;
  }
  get sceneHeight(): number {
    return this.portraitGame ? Math.max(180, this.height * 0.48 - 88) : this.height;
  }
  get panning(): boolean {
    return this.pan !== undefined;
  }
  rotateBy(angle: number): void {
    this.yaw = (this.yaw + angle) % (Math.PI * 2);
    this.refresh();
  }
  private refresh(): void {
    this.projection.update(this.width, this.sceneHeight, this.yaw);
    this.version++;
  }
  resize(width: number, height: number): void {
    this.width = width;
    this.height = height;
    this.refresh();
  }
  lookAt(point: RoomPoint): void {
    this.stopPanning();
    this.yaw = this.projection.bearing(point);
    this.refresh();
  }
  stopPanning(): void {
    this.pan = undefined;
    this.velocity = 0;
  }
  panTo(point: RoomPoint): void {
    const offset = this.projection.bearing(point) - this.yaw;
    const delta = Math.atan2(Math.sin(offset), Math.cos(offset));
    if (
      Math.abs(delta) < 0.001 ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      this.lookAt(point);
      return;
    }
    this.pointer = undefined;
    this.velocity = 0;
    this.pan = { from: this.yaw, delta, started: performance.now() };
  }
  followPet(): void {
    this.pan = undefined;
    this.following = true;
  }
  releaseFollow(): void {
    this.following = false;
  }
  tick(point: RoomPoint): void {
    const now = performance.now(),
      dt = Math.min(0.1, (now - this.last) / 1000);
    this.last = now;
    if (this.held) return;
    if (this.pan) {
      const { from, delta, started } = this.pan;
      const progress = Math.min(1, (now - started) / panDuration);
      this.yaw = (from + delta * (1 - (1 - progress) ** 3)) % (Math.PI * 2);
      this.refresh();
      if (progress === 1) this.pan = undefined;
    } else if (this.following) {
      const target = this.projection.bearing(point);
      const delta = Math.atan2(
        Math.sin(target - this.yaw),
        Math.cos(target - this.yaw),
      );
      if (Math.abs(delta) > 0.00001) this.rotateBy(delta * (1 - Math.exp(-7 * dt)));
    } else if (!this.pointer && Math.abs(this.velocity) > 0.00002) {
      this.rotateBy(this.velocity * dt * 60);
      this.velocity *= Math.exp(-9 * dt);
    }
  }
  setGame(open: boolean, atTable = false): void {
    this.gameOpen = open;
    this.tableGame = atTable;
    this.refresh();
  }
  hold(held: boolean): void {
    this.held = held;
    this.pointer = undefined;
    this.velocity = 0;
    if (held) this.pan = undefined;
  }
  destroy(): void {
    this.controller.abort();
  }
}
