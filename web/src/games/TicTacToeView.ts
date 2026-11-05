import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';

export class TicTacToeView extends GameFrame implements GameView {
  private cells: HTMLButtonElement[] = [];
  private nextButton = this.next();
  constructor(command: Command) {
    super(command);
    const board = element('div', 'ttt-board');
    board.setAttribute('role', 'group');
    board.setAttribute('aria-label', 'Tic-Tac-Toe');
    for (let index = 0; index < 9; index++) {
      const cell = button('', () => this.action('choose', index));
      cell.setAttribute('aria-label', `Feld ${index + 1}`);
      this.cells.push(cell);
      board.append(cell);
    }
    this.content.append(board, this.nextButton);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const board = record(data.board),
      cells = values(board.cells),
      winning = values(board.winning_line);
    this.cells.forEach((control, index) => {
      control.textContent = String(cells[index] ?? '');
      control.disabled =
        !!cells[index] || board.turn !== 'X' || board.winner !== null || !!data.busy;
      control.classList.toggle('winning', winning.includes(index));
    });
    this.nextButton.hidden = board.winner === null || board.winner === undefined;
  }
}
