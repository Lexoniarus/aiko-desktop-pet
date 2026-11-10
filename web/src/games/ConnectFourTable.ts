import type { RoomView } from '../room/RoomView';
import type { PetScreenBounds } from '../room/AikoView';
import { button, element } from '../ui/dom';
import { record, values } from './GameView';
import { columnAt, connectFourGeometry as g, landingCell } from './ConnectFourGeometry';

/** Transparent accessible input; the room scene owns every visible game piece. */
export class ConnectFourTable {
  readonly element = element('section', 'c4-table-scene');
  private board = element('div', 'c4-table-board');
  private columns: HTMLButtonElement[] = [];
  private supply: HTMLButtonElement;
  private scene: ReturnType<RoomView['createConnectFourScene']>;
  private data: Record<string, unknown> = {};
  private gesture?: { id: number; x: number; y: number; pile: boolean; moved: boolean };
  private hover?: number;
  private returning?: { point: { x: number; y: number }; started: number };
  private dragPoint?: { x: number; y: number };
  private previewCell?: number;
  private unsubscribe: () => void;
  private events = new AbortController();

  constructor(
    private room: RoomView,
    private choose: (column: number) => void,
  ) {
    this.element.setAttribute('aria-label', 'Vier gewinnt auf dem Tisch');
    this.scene = room.createConnectFourScene();
    void this.scene.ready.catch(() => {
      const message = element(
        'p',
        'room-message',
        'Die Spielgrafik konnte nicht geladen werden. Bitte schließe das Spiel und öffne es erneut.',
      );
      message.setAttribute('role', 'alert');
      this.element.append(message);
    });
    for (let column = 0; column < g.columns; column++) {
      const target = button('', () => {});
      target.className = 'c4-column-target';
      target.dataset.column = String(column);
      target.setAttribute('aria-label', `Chip in Spalte ${column + 1} einwerfen`);
      target.style.left = `${g.margin + column * g.cell}px`;
      target.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          if (this.legal(column)) this.commit(column);
        }
      });
      target.addEventListener('focus', () => this.showPreview(column));
      target.addEventListener('blur', () => this.showPreview());
      this.columns.push(target);
      this.board.append(target);
    }
    this.supply = button('', () => {});
    this.supply.className = 'c4-player-supply';
    this.supply.setAttribute('aria-label', 'Deinen Chip zum Einwurf ziehen');
    this.element.append(this.board, this.supply);
    const options = { signal: this.events.signal };
    this.element.addEventListener('pointerdown', this.down, options);
    this.element.addEventListener('pointermove', this.move, options);
    this.element.addEventListener('pointerup', this.up, options);
    this.element.addEventListener('pointercancel', this.cancel, options);
    this.element.addEventListener(
      'lostpointercapture',
      (event) => {
        if (this.gesture?.id === event.pointerId) this.cancel();
      },
      options,
    );
    window.addEventListener('blur', this.cancel, options);
    document.addEventListener('visibilitychange', this.cancel, options);
    this.board.addEventListener(
      'pointerleave',
      () => {
        if (!this.gesture) this.showPreview();
      },
      options,
    );
    this.unsubscribe = room.followPet((bounds) => this.draw(bounds));
  }

  update(data: Record<string, unknown>): void {
    this.data = data;
    this.scene.update(data);
    this.columns.forEach((target, index) => {
      target.disabled = !this.legal(index);
    });
    this.supply.disabled = !this.legal();
    this.element.setAttribute('aria-busy', String(!!data.preparing || !!data.busy));
    if (this.gesture && !this.legal()) this.cancel();
    this.showPreview(this.hover);
  }
  private legal(column?: number): boolean {
    const board = record(this.data.board);
    return (
      !this.data.preparing &&
      !this.data.busy &&
      board.turn === 1 &&
      board.winner === null &&
      (column === undefined || landingCell(values(board.cells), column) !== undefined)
    );
  }
  private commit(column: number): void {
    this.update({ ...this.data, busy: true });
    this.choose(column);
  }
  private local(event: PointerEvent) {
    const box = this.board.getBoundingClientRect();
    return {
      x: ((event.clientX - box.left) * g.size) / box.width,
      y: ((event.clientY - box.top) * g.size) / box.height,
    };
  }
  private at(event: PointerEvent, entryOnly: boolean): number | undefined {
    const point = this.local(event);
    if (
      point.y < g.entry - 60 ||
      point.y > (entryOnly ? g.top + 12 : g.top + 6 * g.cell)
    )
      return;
    const column = columnAt(point.x);
    return column !== undefined && this.legal(column) ? column : undefined;
  }
  private down = (event: PointerEvent): void => {
    if (!event.isPrimary || event.button !== 0 || !this.legal() || this.gesture) return;
    const target = event.target as HTMLElement;
    const pile = this.supply.contains(target);
    if (!pile && !target.closest('.c4-column-target')) return;
    this.returning = undefined;
    this.dragPoint = undefined;
    this.gesture = {
      id: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      pile,
      moved: false,
    };
    this.element.setPointerCapture(event.pointerId);
    this.room.camera.hold(true);
    this.showPreview(this.at(event, pile));
    event.preventDefault();
    event.stopPropagation();
  };
  private move = (event: PointerEvent): void => {
    const gesture = this.gesture;
    if (!gesture) {
      if (event.pointerType === 'mouse') this.showPreview(this.at(event, false));
      return;
    }
    if (event.pointerId !== gesture.id) return;
    gesture.moved ||=
      Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) > 6;
    this.showPreview(this.at(event, gesture.pile || gesture.moved));
    if (gesture.moved) this.dragPoint = this.local(event);
    event.preventDefault();
  };
  private up = (event: PointerEvent): void => {
    const gesture = this.gesture;
    if (!gesture || event.pointerId !== gesture.id) return;
    const column = this.at(event, gesture.pile || gesture.moved),
      point = this.local(event);
    this.release();
    if (column !== undefined) {
      this.dragPoint = undefined;
      this.commit(column);
    } else if (gesture.moved) {
      this.returning = { point, started: performance.now() };
    } else this.dragPoint = undefined;
    event.preventDefault();
  };
  private release(): void {
    const id = this.gesture?.id;
    this.gesture = undefined;
    if (id !== undefined && this.element.hasPointerCapture(id))
      this.element.releasePointerCapture(id);
    this.room.camera.hold(false);
    this.showPreview();
  }
  private cancel = (): void => {
    this.returning = undefined;
    this.dragPoint = undefined;
    if (this.gesture) this.release();
    else this.showPreview();
  };
  private showPreview(column?: number): void {
    this.hover = column;
    this.previewCell =
      column !== undefined && this.legal(column)
        ? landingCell(values(record(this.data.board).cells), column)
        : undefined;
  }
  private position(node: HTMLElement, point: { x: number; y: number }): void {
    node.style.left = `${point.x}px`;
    node.style.top = `${point.y}px`;
  }
  private draw(bounds: PetScreenBounds): void {
    const frame = this.room.tableGameFrame();
    if (!frame) return;
    this.board.style.transform = `translate(${frame.x}px, ${frame.y}px) scale(${frame.scale})`;
    this.position(this.supply, { x: frame.playerX, y: frame.playerY });
    this.supply.style.setProperty('--chip-size', `${frame.chip}px`);
    if (this.returning) {
      const t = Math.min(1, (performance.now() - this.returning.started) / 160);
      const eased = t * (2 - t);
      const end = {
        x: (frame.playerX - frame.x) / frame.scale,
        y: (frame.playerY - frame.y) / frame.scale,
      };
      this.dragPoint =
        t < 1
          ? {
              x: this.returning.point.x + (end.x - this.returning.point.x) * eased,
              y: this.returning.point.y + (end.y - this.returning.point.y) * eased,
            }
          : undefined;
      if (t === 1) this.returning = undefined;
    }
    this.scene.draw(
      frame,
      bounds,
      this.room.heldGameChip,
      this.previewCell,
      this.dragPoint,
    );
  }
  destroy(): void {
    this.cancel();
    this.events.abort();
    this.unsubscribe();
    this.scene.destroy();
    this.element.remove();
  }
}
