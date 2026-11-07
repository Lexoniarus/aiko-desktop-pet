import type { RoomView } from '../room/RoomView';
import type { PetScreenBounds } from '../room/AikoView';
import type { RoomArtwork } from '../ui/RoomArtwork';
import { button, element } from '../ui/dom';
import { record, values } from './GameView';
import {
  cellPoint,
  chipPoint,
  columnAt,
  connectFourGeometry as g,
  landingCell,
} from './ConnectFourGeometry';

/** Table-bound artwork and input. Only Python commits moves. */
export class ConnectFourTable {
  readonly element = element('section', 'c4-table-scene');
  private board = element('div', 'c4-table-board');
  private cells: HTMLImageElement[] = [];
  private columns: HTMLButtonElement[] = [];
  private moving: HTMLImageElement;
  private preview: HTMLImageElement;
  private landing = element('span', 'c4-landing');
  private dragged: HTMLImageElement;
  private supply: HTMLButtonElement;
  private aikoPile: HTMLImageElement[] = [];
  private data: Record<string, unknown> = {};
  private received = 0;
  private flightKey: unknown;
  private flightStart = { x: 0, y: 0 };
  private gesture?: { id: number; x: number; y: number; pile: boolean; moved: boolean };
  private hover?: number;
  private returning?: Animation;
  private unsubscribe: () => void;
  private events = new AbortController();

  constructor(
    private room: RoomView,
    private art: RoomArtwork,
    private choose: (column: number) => void,
  ) {
    this.element.setAttribute('aria-label', 'Vier gewinnt auf dem Tisch');
    for (let cell = 0; cell < g.columns * g.rows; cell++) {
      const hole = element('span', 'c4-table-hole');
      this.position(hole, cellPoint(cell));
      this.board.append(hole);
      const image = art.image('', '', 'c4-table-chip');
      image.dataset.cell = String(cell);
      this.position(image, cellPoint(cell));
      this.cells.push(image);
      this.board.append(image);
    }
    const face = art.image(art.game('c4-board'), 'Vier gewinnt', 'c4-table-face');
    this.moving = art.image('', '', 'c4-table-chip c4-moving');
    this.preview = art.image(art.game('c4-yellow'), '', 'c4-table-chip c4-preview');
    this.dragged = art.image(art.game('c4-yellow'), '', 'c4-table-chip c4-dragged');
    this.moving.hidden =
      this.preview.hidden =
      this.dragged.hidden =
      this.landing.hidden =
        true;
    this.board.append(this.moving, face, this.preview, this.landing, this.dragged);
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
    for (let index = 0; index < 3; index++) {
      const chip = art.image(art.game('c4-yellow'));
      chip.style.setProperty('--stack-index', String(index));
      this.supply.append(chip);
      const red = art.image(art.game('c4-pile'), '', 'c4-aiko-supply');
      this.aikoPile.push(red);
      this.element.append(red);
    }
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
    this.received = performance.now();
    const board = record(data.board),
      cells = values(board.cells);
    const winning = values(board.winning_line ?? board.winning_cells);
    const motion = record(record(data.props).motion),
      drop = record(data.drop);
    const hidden = Number(motion.kind === 'chip' ? motion.cell : (drop.cell ?? -1));
    this.cells.forEach((image, index) => {
      const player = Number(cells[index] ?? 0);
      image.hidden = !player || index === hidden;
      if (player) image.src = this.art.game(player === 1 ? 'c4-yellow' : 'c4-red');
      image.classList.toggle('winning', winning.includes(index));
    });
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
    this.returning?.cancel();
    this.dragged.hidden = true;
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
    this.dragged.hidden = !gesture.moved;
    if (gesture.moved) this.position(this.dragged, this.local(event));
    event.preventDefault();
  };
  private up = (event: PointerEvent): void => {
    const gesture = this.gesture;
    if (!gesture || event.pointerId !== gesture.id) return;
    const column = this.at(event, gesture.pile || gesture.moved),
      point = this.local(event);
    this.release();
    if (column !== undefined) {
      this.dragged.hidden = true;
      this.commit(column);
    } else if (gesture.moved) {
      const frame = this.room.tableGameFrame();
      if (frame) {
        const end = {
          x: (frame.playerX - frame.x) / frame.scale,
          y: (frame.playerY - frame.y) / frame.scale,
        };
        this.returning = this.dragged.animate(
          [
            { left: `${point.x}px`, top: `${point.y}px` },
            { left: `${end.x}px`, top: `${end.y}px` },
          ],
          { duration: 160, easing: 'ease-out' },
        );
        void this.returning.finished
          .then(() => {
            this.dragged.hidden = true;
          })
          .catch(() => {});
      }
    } else this.dragged.hidden = true;
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
    this.returning?.cancel();
    this.dragged.hidden = true;
    if (this.gesture) this.release();
    else this.showPreview();
  };
  private showPreview(column?: number): void {
    this.hover = column;
    const cell =
      column !== undefined && this.legal(column)
        ? landingCell(values(record(this.data.board).cells), column)
        : undefined;
    this.preview.hidden = this.landing.hidden = cell === undefined;
    if (cell !== undefined) {
      this.position(this.preview, { x: cellPoint(cell).x, y: g.entry });
      this.position(this.landing, cellPoint(cell));
    }
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
    this.aikoPile.forEach((chip, index) => {
      this.position(chip, {
        x: bounds.originX + 80 * bounds.scale,
        y: bounds.originY + 178 * bounds.scale - index * 4 * frame.scale,
      });
      chip.style.width = `${frame.chip}px`;
      chip.hidden =
        !!this.data.preparing ||
        (index === 2 &&
          (this.room.heldGameChip ||
            record(record(this.data.props).motion).kind === 'chip'));
    });
    const elapsed = performance.now() - this.received;
    const motion = record(record(this.data.props).motion),
      drop = record(this.data.drop);
    this.moving.hidden = true;
    if (motion.kind === 'chip') {
      if (motion.id !== this.flightKey) {
        this.flightKey = motion.id;
        this.flightStart = {
          x: (bounds.originX + 96 * bounds.scale - frame.x) / frame.scale,
          y: (bounds.originY + 141 * bounds.scale - frame.y) / frame.scale,
        };
      }
      const fraction = Math.min(
        1,
        Number(motion.fraction) + elapsed / Number(motion.duration),
      );
      const flightFraction = Number(motion.flight_duration) / Number(motion.duration);
      this.position(
        this.moving,
        chipPoint(this.flightStart, Number(motion.cell), fraction, flightFraction),
      );
      this.moving.src = this.art.game('c4-red');
      this.moving.style.zIndex = fraction < flightFraction ? '3' : '1';
      this.moving.hidden = false;
    } else if (Number(drop.cell ?? -1) >= 0 && Number(drop.fraction) >= 0) {
      const target = cellPoint(Number(drop.cell)),
        fraction = Math.min(1, Number(drop.fraction) + elapsed / 180);
      this.position(this.moving, {
        x: target.x,
        y: g.entry + (target.y - g.entry) * fraction,
      });
      this.moving.src = this.art.game(
        Number(drop.player) === 1 ? 'c4-yellow' : 'c4-red',
      );
      this.moving.style.zIndex = '1';
      this.moving.hidden = false;
    }
  }
  destroy(): void {
    this.cancel();
    this.events.abort();
    this.unsubscribe();
    this.element.remove();
  }
}
