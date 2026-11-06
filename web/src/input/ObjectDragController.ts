import type { FederatedPointerEvent } from 'pixi.js';
import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomCommandName } from '../bridge/commands';
import type { RoomPoint } from '../room/RoomLayout';
import type { DragPlacement, RoomView } from '../room/RoomView';
import { PointerDrag } from './PointerDrag';
import type { DragPointer } from './PointerDrag';

export class ObjectDragController {
  onDragBegin: () => void = () => {};
  onError: (error: unknown) => void = () => {};
  private gesture = new PointerDrag();
  private settling = false;
  constructor(
    private room: RoomView,
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
    let ground: RoomPoint = item?.position
      ? { x: item.position.x, depth: this.room.objectDepth(item.instance_id) }
      : { ...(this.room.petPosition ?? { x: 400, depth: 100 }) };
    let pending: DragPlacement | undefined;
    let sending: Promise<void> | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let finished = false;
    const send = (): void => {
      if (sending || timer || !pending || finished) return;
      timer = setTimeout(() => {
        timer = undefined;
        sending = (async () => {
          if (!(await reservation)) return;
          if (pending && !finished) {
            const pose = pending;
            pending = undefined;
            await this.request('object_drag_move', { ...pose });
          }
        })()
          .catch(this.onError)
          .finally(() => {
            sending = undefined;
            send();
          });
      }, 75);
    };
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
        this.room.dragging = true;
        this.room.draggingInstance = item?.instance_id;
        reservation = this.request(
          'object_drag_start',
          item
            ? {
                instance: item.instance_id,
                revision: item.revision,
              }
            : { definition },
        ).then(
          () => true,
          (error) => {
            this.onError(error);
            return false;
          },
        );
        document.body.append(ghost);
      },
      move: (x, y) => {
        const target = this.dropTarget(x, y, ground, definition);
        if (target.inside) ground = { x: target.x, depth: target.depth };
        pending = target;
        send();
        const [width, height] = this.room.portionSizeAt(
          definition,
          ground.depth,
          ground.x,
        );
        ghost.style.width = `${width}px`;
        ghost.style.height = `${height}px`;
        ghost.style.transform = `translate(${x}px,${y}px) translate(${(-100 * asset!.pivot[0]) / asset!.dimensions[0]}%,${(-100 * asset!.pivot[1]) / asset!.dimensions[1]}%)`;
        ghost.classList.toggle('invalid-drop', !target.inside);
        this.room.dragVisual = { x, y };
      },
      finish: (x, y, dragged, cancelled) => {
        finished = true;
        clearTimeout(timer);
        pending = undefined;
        this.room.camera.hold(false);
        if (dragged) this.room.suppressPetTap();
        this.settling = true;
        void (async () => {
          try {
            if (!(await reservation)) return;
            await sending;
            if (!dragged) return;
            const target = this.dropTarget(x, y, ground, definition);
            if (cancelled || !target.inside) await this.request('object_drag_cancel');
            else {
              await this.request('object_drag_move', { ...target });
              await this.request('object_drag_drop', { ...target });
            }
          } catch (error) {
            if (dragged) await this.request('object_drag_cancel').catch(() => {});
            this.onError(error);
          } finally {
            this.room.draggingInstance = undefined;
            this.room.dragging = false;
            this.room.dragVisual = undefined;
            ghost.remove();
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
    ground: RoomPoint,
    definition: string,
  ): DragPlacement {
    const overlay = document
      .elementFromPoint(x, y)
      ?.closest('button,input,select,dialog,a');
    const point = this.room.dragPoint(x, y, ground, definition);
    return overlay ? { ...point, inside: false, offer: false } : point;
  }
  cancel(): void {
    this.gesture.cancel();
  }
}
