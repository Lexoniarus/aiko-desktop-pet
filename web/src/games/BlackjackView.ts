import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';

export class BlackjackView extends GameFrame implements GameView {
  private table = element('div', 'blackjack-table');
  private hit = button('Karte', () => this.action('hit'));
  private stand = button('Bleiben', () => this.action('stand'));
  private signature = '';
  constructor(
    command: Command,
    private art: RoomArtwork,
  ) {
    super(command);
    this.element.dataset.game = 'blackjack';
    this.table.classList.add('bj-player');
    this.table.style.backgroundImage = `url("${art.game('blackjack-table')}")`;
    this.content.append(this.table, this.hit, this.stand);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const table = record(data.table);
    const signature = JSON.stringify(table);
    if (signature !== this.signature) {
      this.signature = signature;
      this.table.replaceChildren();
      for (const [title, key] of [['Deine Karten', 'player']]) {
        const hand = element('div', 'card-hand');
        hand.append(element('h3', '', title!));
        for (const [index, value] of values(table[key!]).entries()) {
          const card = record(value),
            image = element('img');
          image.src = this.art.file(
            `playing_cards/${value ? `card_${card.suit}_${card.rank}.png` : 'card_back.png'}`,
          );
          image.dataset.cardIndex = String(index);
          image.draggable = false;
          image.alt = value ? `${card.rank} ${card.suit}` : 'Verdeckte Karte';
          hand.append(image);
        }
        this.table.append(hand);
      }
      this.table.append(element('p', '', `Deine Punkte: ${table.player_total ?? '–'}`));
    }
    const allowed = table.phase === 'player' && !data.busy;
    this.hit.disabled = this.stand.disabled = !allowed;
    this.table.querySelector('.bj-card-target')?.remove();
    const motion = record(record(data.props).motion);
    if (motion.kind === 'player') {
      const target = element('span', 'bj-card-target');
      target.setAttribute('aria-hidden', 'true');
      this.table.querySelector('.card-hand')?.append(target);
    }
    this.status.textContent = table.result
      ? table.result === 'win'
        ? 'Du gewinnst.'
        : table.result === 'loss'
          ? 'Aiko gewinnt.'
          : 'Unentschieden.'
      : allowed
        ? 'Noch eine Karte oder bleiben?'
        : 'Aiko gibt die Karten.';
  }
}
