import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';

export class TicTacToeView extends GameFrame implements GameView {
  private cells: HTMLButtonElement[] = [];
  private nextButton = this.next();
  constructor(
    command: Command,
    private art: RoomArtwork,
  ) {
    super(command);
    const board = element('div', 'ttt-board');
    board.style.backgroundImage = `url("${art.game('ttt-frame')}")`;
    board.setAttribute('role', 'group');
    board.setAttribute('aria-label', 'Tic-Tac-Toe');
    for (let index = 0; index < 9; index++) {
      const cell = button('', () => this.action('choose', index));
      cell.setAttribute('aria-label', `Feld ${index + 1}`);
      cell.style.left = `${((28 + (index % 3) * 101) / 350) * 100}%`;
      cell.style.top = `${((28 + Math.floor(index / 3) * 101) / 350) * 100}%`;
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
      const mark = String(cells[index] ?? '');
      if (control.dataset.mark !== mark) {
        control.dataset.mark = mark;
        control.replaceChildren();
        if (mark)
          control.append(
            this.art.image(this.art.icon(`play_ttt_${mark.toLowerCase()}`, 64), mark),
          );
      }
      control.disabled =
        !!cells[index] || board.turn !== 'X' || board.winner !== null || !!data.busy;
      control.classList.toggle('winning', winning.includes(index));
    });
    this.nextButton.hidden = board.winner === null || board.winner === undefined;
    this.status.textContent = board.winner
      ? board.winner === 'X'
        ? 'Du gewinnst.'
        : board.winner === 'O'
          ? 'Aiko gewinnt.'
          : 'Unentschieden.'
      : board.turn === 'X' && !data.busy
        ? 'Du bist am Zug.'
        : 'Aiko ist am Zug.';
  }
}
