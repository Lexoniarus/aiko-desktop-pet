export interface DragPointer {
  pointerId: number;
  clientX: number;
  clientY: number;
  button: number;
  isPrimary: boolean;
}
export interface DragHandlers {
  start(): void;
  move(x: number, y: number): void;
  finish(x: number, y: number, dragged: boolean, cancelled: boolean): void;
}

/** One captured pointer, also when the original button/panel is removed. */
export class PointerDrag {
  private end?: () => void;
  begin(event: DragPointer, handlers: DragHandlers): boolean {
    if (this.end || event.button !== 0 || !event.isPrimary) return false;
    const owner = document.documentElement;
    let dragged = false;
    const eatClick = (click: MouseEvent): void => {
      click.preventDefault();
      click.stopImmediatePropagation();
    };
    const finish = (x: number, y: number, cancelled: boolean): void => {
      this.end = undefined;
      window.removeEventListener('pointermove', move, true);
      window.removeEventListener('pointerup', up, true);
      window.removeEventListener('pointercancel', cancel, true);
      window.removeEventListener('blur', blur);
      document.removeEventListener('visibilitychange', visibility);
      owner.removeEventListener('lostpointercapture', lost);
      if (owner.hasPointerCapture(event.pointerId))
        owner.releasePointerCapture(event.pointerId);
      handlers.finish(x, y, dragged, cancelled);
      setTimeout(() => document.removeEventListener('click', eatClick, true), 0);
    };
    const move = (pointer: PointerEvent): void => {
      if (pointer.pointerId !== event.pointerId) return;
      if (
        !dragged &&
        Math.hypot(pointer.clientX - event.clientX, pointer.clientY - event.clientY) >=
          8
      ) {
        dragged = true;
        document.addEventListener('click', eatClick, true);
        handlers.start();
      }
      if (dragged) {
        pointer.preventDefault();
        handlers.move(pointer.clientX, pointer.clientY);
      }
    };
    const up = (pointer: PointerEvent): void => {
      if (pointer.pointerId === event.pointerId)
        finish(pointer.clientX, pointer.clientY, false);
    };
    const cancel = (pointer: PointerEvent): void => {
      if (pointer.pointerId === event.pointerId)
        finish(pointer.clientX, pointer.clientY, true);
    };
    const blur = (): void => finish(event.clientX, event.clientY, true);
    const visibility = (): void => {
      if (document.hidden) blur();
    };
    const lost = (pointer: PointerEvent): void => {
      if (pointer.pointerId === event.pointerId) blur();
    };
    try {
      owner.setPointerCapture(event.pointerId);
    } catch {
      return false;
    }
    this.end = blur;
    window.addEventListener('pointermove', move, { capture: true, passive: false });
    window.addEventListener('pointerup', up, true);
    window.addEventListener('pointercancel', cancel, true);
    window.addEventListener('blur', blur);
    document.addEventListener('visibilitychange', visibility);
    owner.addEventListener('lostpointercapture', lost);
    return true;
  }
  cancel(): void {
    this.end?.();
  }
}
