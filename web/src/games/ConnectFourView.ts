import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';

export class ConnectFourView extends GameFrame implements GameView {
  private columns: HTMLButtonElement[] = [];
  private cells: HTMLElement[] = [];
  private nextButton = this.next();
  constructor(command: Command) {
    super(command);
    const controls = element('div', 'c4-columns'),
      board = element('div', 'c4-board');
    for (let column = 0; column < 7; column++) {
      const control = button(String(column + 1), () => this.action('choose', column));
      control.setAttribute('aria-label', `Stein in Spalte ${column + 1}`);
      this.columns.push(control);
      controls.append(control);
    }
    for (let cell = 0; cell < 42; cell++) {
      const node = element('span', 'c4-cell');
      this.cells.push(node);
      board.append(node);
    }
    this.content.append(controls, board, this.nextButton);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const board = record(data.board),
      cells = values(board.cells),
      winning = values(board.winning_line ?? board.winning_cells);
    this.cells.forEach((node, index) => {
      node.dataset.player = String(cells[index] ?? 0);
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
  }
}
