import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';

export class ConnectFourView extends GameFrame implements GameView {
  private columns: HTMLButtonElement[] = [];
  private cells: HTMLElement[] = [];
  private nextButton = this.next();
  private falling: HTMLElement;
  constructor(
    command: Command,
    private art: RoomArtwork,
  ) {
    super(command);
    const controls = element('div', 'c4-columns'),
      board = element('div', 'c4-board');
    this.element.dataset.game = 'connect-four';
    board.style.backgroundImage = `url("${art.game('c4-board')}")`;
    for (let column = 0; column < 7; column++) {
      const control = button(String(column + 1), () => this.action('choose', column));
      control.setAttribute('aria-label', `Stein in Spalte ${column + 1}`);
      this.columns.push(control);
      controls.append(control);
    }
    for (let cell = 0; cell < 42; cell++) {
      const node = element('span', 'c4-cell');
      node.dataset.cell = String(cell);
      node.style.left = `${((100 + (cell % 7) * 40) / 480) * 100}%`;
      node.style.top = `${((112 + Math.floor(cell / 7) * 40) / 480) * 100}%`;
      this.cells.push(node);
      board.append(node);
    }
    this.falling = art.image(art.game('c4-red'), '', 'c4-falling');
    this.falling.hidden = true;
    board.append(this.falling);
    this.content.append(controls, board, this.nextButton);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const board = record(data.board),
      cells = values(board.cells),
      winning = values(board.winning_line ?? board.winning_cells);
    this.cells.forEach((node, index) => {
      node.dataset.player = String(cells[index] ?? 0);
      const player = Number(cells[index] ?? 0);
      node.style.backgroundImage = player
        ? `url("${this.art.game(player === 1 ? 'c4-yellow' : 'c4-red')}")`
        : '';
      node.classList.toggle('winning', winning.includes(index));
      node.setAttribute(
        'aria-label',
        `Feld ${index + 1}: ${cells[index] === 1 ? 'Dein Stein' : cells[index] === 2 ? 'Aikos Stein' : 'leer'}`,
      );
    });
    this.columns.forEach((control, index) => {
      control.disabled =
        !!data.busy || board.turn !== 1 || board.winner !== null || cells[index] !== 0;
    });
    this.nextButton.hidden = board.winner === null || board.winner === undefined;
    const drop = record(data.drop),
      fraction = Number(drop.fraction ?? -1),
      cell = Number(drop.cell ?? -1);
    this.falling.hidden = cell < 0 || fraction < 0;
    if (!this.falling.hidden) {
      const player = Number(drop.player);
      (this.falling as HTMLImageElement).src = this.art.game(
        player === 1 ? 'c4-yellow' : 'c4-red',
      );
      this.falling.style.left = `${((100 + ((cell % 7) + 0.5) * 40) / 480) * 100}%`;
      this.falling.style.top = `${((92 + (Math.floor(cell / 7) * 40 + 40) * fraction) / 480) * 100}%`;
    }
    if (cell >= 0) this.cells[cell]!.style.backgroundImage = '';
    this.status.textContent =
      board.winner !== null && board.winner !== undefined
        ? board.winner === 1
          ? 'Du gewinnst.'
          : board.winner === 2
            ? 'Aiko gewinnt.'
            : 'Unentschieden.'
        : board.turn === 1 && !data.busy
          ? 'Wähle eine Spalte.'
          : 'Aiko ist am Zug.';
  }
}
