import type { FederatedPointerEvent } from 'pixi.js';
import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import { delta } from '../room/RoomProjection';
import type { Command } from '../ui/dom';

export class ObjectDragController {
  onDragBegin: () => void = () => {};
  private cancelDrag: (() => void) | undefined;
  constructor(
    private room: RoomView,
    private command: Command,
  ) {
    room.onObjectDown = (item, event) => this.existing(item, event);
  }
  private nearAiko(point: { x: number; depth: number }): boolean {
    const pet = this.room.petPosition;
    return (
      !!pet && Math.hypot(delta(pet.x, point.x), (pet.depth - point.depth) * 475) < 180
    );
  }
  private existing(
    item: RoomSnapshot['objects'][number],
    event: FederatedPointerEvent,
  ): void {
    if (item.state !== 'resting') return;
    event.stopPropagation();
    this.begin(event.clientX, event.clientY, async (x, y) => {
      const point = this.room.pointAt(x, y);
      if (this.nearAiko(point))
        await this.command('offer', {
          instance: item.instance_id,
          revision: item.revision,
        });
      else
        await this.command('move', {
          instance: item.instance_id,
          revision: item.revision,
          ...point,
        });
    });
  }
  bindSupply(control: HTMLElement, definition: string): void {
    control.addEventListener('pointerdown', (event) => {
      if (event.button !== 0) return;
      this.begin(
        event.clientX,
        event.clientY,
        async (x, y) => {
          const point = this.room.pointAt(x, y);
          await this.command(this.nearAiko(point) ? 'offer' : 'place', {
            definition,
            ...point,
          });
        },
        definition,
      );
    });
  }
  private begin(
    x: number,
    y: number,
    drop: (x: number, y: number) => Promise<void>,
    definition?: string,
  ): void {
    this.cancelDrag?.();
    this.room.camera.hold(true);
    let moved = false;
    const ghost = document.createElement('img');
    ghost.className = 'drag-portion';
    const asset = definition && this.room.assets.items[definition];
    if (asset) ghost.src = new URL(asset.file, this.room.root).href;
    const move = (event: PointerEvent) => {
      if (!moved && Math.hypot(event.clientX - x, event.clientY - y) > 8) {
        moved = true;
        this.onDragBegin();
      }
      if (moved && asset) {
        if (!ghost.isConnected) document.body.append(ghost);
        ghost.style.transform = `translate(${event.clientX}px,${event.clientY}px)`;
      }
    };
    const clear = () => {
      ghost.remove();
      this.room.camera.hold(false);
      this.cancelDrag = undefined;
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointercancel', cancel);
    };
    const up = (event: PointerEvent) => {
      clear();
      const rect = this.room.app.canvas.getBoundingClientRect();
      if (
        moved &&
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom
      ) {
        event.preventDefault();
        void drop(event.clientX, event.clientY);
      }
    };
    const cancel = () => clear();
    this.cancelDrag = cancel;
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    window.addEventListener('pointercancel', cancel);
  }
  cancel(): void {
    this.cancelDrag?.();
  }
}
