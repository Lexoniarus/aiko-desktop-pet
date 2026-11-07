import type { Command } from '../ui/dom';
import { GameFrame, record } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';
import type { RoomView } from '../room/RoomView';
import { ConnectFourTable } from './ConnectFourTable';

/** Compact controls; pieces and direct input live on the actual table. */
export class ConnectFourView extends GameFrame implements GameView {
  private nextButton = this.next();
  private table: ConnectFourTable;
  constructor(command: Command, art: RoomArtwork, room: RoomView, host: HTMLElement) {
    super(command);
    this.element.dataset.game = 'connect-four';
    this.table = new ConnectFourTable(room, art, (column) =>
      this.action('choose', column),
    );
    host.append(this.table.element);
    this.content.append(this.nextButton);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    this.table.update(data);
    const board = record(data.board);
    this.nextButton.hidden =
      board.winner === null || board.winner === undefined || !!data.busy;
    this.status.textContent = data.preparing
      ? 'Aiko kommt zum Tisch ...'
      : board.winner !== null && board.winner !== undefined
        ? board.winner === 1
          ? 'Du gewinnst.'
          : board.winner === 2
            ? 'Aiko gewinnt.'
            : 'Unentschieden.'
        : board.turn === 1 && !data.busy
          ? 'Ziehe deinen Chip zum Einwurf oder tippe eine Spalte an.'
          : 'Aiko ist am Zug.';
  }
  destroy(): void {
    this.table.destroy();
  }
}
