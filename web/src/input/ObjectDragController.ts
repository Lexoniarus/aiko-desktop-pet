import type { FederatedPointerEvent } from 'pixi.js';
import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomCommandName } from '../bridge/commands';
import type { RoomView } from '../room/RoomView';
import type { Command } from '../ui/dom';
import { PointerDrag } from './PointerDrag';
import type { DragPointer } from './PointerDrag';

export class ObjectDragController {
  onDragBegin: () => void = () => {};
  onError: (error: unknown) => void = () => {};
  private gesture = new PointerDrag();
  private settling = false;
  constructor(
    private room: RoomView,
    private command: Command,
    private request: (
      name: RoomCommandName,
      args?: Record<string, unknown>,
    ) => Promise<void>,
  ) {
    room.onObjectDown = (item, event) => this.existing(item, event);
  }
  private existing(
    item: RoomSnapshot['objects'][number],
    event: FederatedPointerEvent,
  ): void {
    if (item.state !== 'resting') return;
    event.stopPropagation();
    this.begin(event, item.definition_id, item);
  }
  bindSupply(control: HTMLElement, definition: string): void {
    control.addEventListener('pointerdown', (event) => {
      if (event.button === 0 && event.isPrimary) {
        event.preventDefault();
        this.begin(event, definition);
      }
    });
  }
  private begin(
    event: DragPointer,
    definition: string,
    item?: RoomSnapshot['objects'][number],
  ): void {
    if (this.settling) return;
    let reservation = Promise.resolve(true);
    const ghost = document.createElement('img');
    ghost.className = 'drag-portion';
    ghost.draggable = false;
    ghost.alt = '';
    const asset = this.room.assets.items[definition];
    if (asset) ghost.src = new URL(asset.file, this.room.root).href;
    const accepted = this.gesture.begin(event, {
      start: () => {
        this.onDragBegin();
        this.room.suppressPetTap();
        if (item) {
          this.room.draggingInstance = item.instance_id;
          reservation = this.request('object_drag_start', {
            instance: item.instance_id,
            revision: item.revision,
          }).then(
            () => true,
            (error) => {
              this.onError(error);
              return false;
            },
          );
        }
        document.body.append(ghost);
      },
      move: (x, y) => {
        const [width, height] = this.room.portionSize(definition, x, y);
        ghost.style.width = `${width}px`;
        ghost.style.height = `${height}px`;
        ghost.style.transform = `translate(${x}px,${y}px) translate(-50%,${this.room.floorPoint(x, y) ? '-100%' : '-50%'})`;
        ghost.classList.toggle('invalid-drop', !this.dropTarget(x, y));
      },
      finish: (x, y, dragged, cancelled) => {
        ghost.remove();
        this.room.camera.hold(false);
        if (dragged) this.room.suppressPetTap();
        this.settling = true;
        void (async () => {
          try {
            if (!(await reservation)) return;
            const target = !cancelled && dragged ? this.dropTarget(x, y) : undefined;
            if (item && dragged) {
              if (target) await this.request('object_drag_drop', target);
              else await this.request('object_drag_cancel');
            } else if (target)
              await this.command(target.offer ? 'offer' : 'place', {
                definition,
                x: target.x,
                depth: target.depth,
              });
          } catch (error) {
            if (item) await this.request('object_drag_cancel').catch(() => {});
            this.onError(error);
          } finally {
            this.room.draggingInstance = undefined;
            this.settling = false;
          }
        })();
      },
    });
    if (accepted) this.room.camera.hold(true);
  }
  private dropTarget(
    x: number,
    y: number,
  ): { x: number; depth: number; offer: boolean } | undefined {
    const overlay = document
      .elementFromPoint(x, y)
      ?.closest('button,input,select,dialog,a');
    if (overlay) return;
    if (this.room.petContains(x, y)) {
      const pet = this.room.petPosition!;
      return { ...pet, offer: true };
    }
    const point = this.room.floorPoint(x, y);
    return point ? { ...point, offer: false } : undefined;
  }
  cancel(): void {
    this.gesture.cancel();
  }
}
