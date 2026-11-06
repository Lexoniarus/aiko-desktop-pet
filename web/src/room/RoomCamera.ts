import type { RoomPoint, RoomLayout } from './RoomLayout';
import { RoomProjection } from './RoomProjection';

export class RoomCamera {
  readonly projection: RoomProjection;
  yaw = 0;
  version = 0;
  following = false;
  private held = false;
  private gameOpen = false;
  private width = 1;
  private height = 1;
  private pointer?: { id: number; x: number; moved: boolean };
  private velocity = 0;
  private last = performance.now();
  private lastDragAt = -Infinity;
  get blocksTap(): boolean {
    return performance.now() - this.lastDragAt < 350;
  }
  private controller = new AbortController();
  constructor(
    private canvas: HTMLCanvasElement,
    readonly layout: RoomLayout,
  ) {
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
    return this.gameOpen && this.height > this.width;
  }
  get sceneHeight(): number {
    return this.portraitGame ? Math.max(180, this.height * 0.48 - 88) : this.height;
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
    this.yaw = Math.atan2(
      point.x - this.layout.width / 2,
      this.layout.depth / 2 - point.depth,
    );
    this.velocity = 0;
    this.refresh();
  }
  followPet(): void {
    this.following = true;
  }
  releaseFollow(): void {
    this.following = false;
  }
  tick(point: RoomPoint): void {
    const now = performance.now(),
      dt = Math.min(0.1, (now - this.last) / 1000);
    this.last = now;
    if (this.following) {
      const target = Math.atan2(
        point.x - this.layout.width / 2,
        this.layout.depth / 2 - point.depth,
      );
      const delta = Math.atan2(
        Math.sin(target - this.yaw),
        Math.cos(target - this.yaw),
      );
      if (Math.abs(delta) > 0.00001) this.rotateBy(delta * (1 - Math.exp(-7 * dt)));
    } else if (!this.pointer && !this.held && Math.abs(this.velocity) > 0.00002) {
      this.rotateBy(this.velocity * dt * 60);
      this.velocity *= Math.exp(-9 * dt);
    }
  }
  setGame(open: boolean): void {
    this.gameOpen = open;
    this.refresh();
  }
  hold(held: boolean): void {
    this.held = held;
    this.pointer = undefined;
    this.velocity = 0;
  }
  destroy(): void {
    this.controller.abort();
  }
}
