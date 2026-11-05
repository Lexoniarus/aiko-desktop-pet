import { element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';

export class RockPaperScissorsView extends GameFrame implements GameView {
  private hand = element('div', 'rps-player-hand');
  private face = element('img');
  private waiting = element('span', '', 'Wähle deine Hand');
  private choices: HTMLButtonElement[] = [];
  constructor(
    command: Command,
    private art: RoomArtwork,
  ) {
    super(command);
    this.element.dataset.game = 'rps';
    this.hand.style.backgroundImage = `url("${art.game('rps-mat')}")`;
    this.face.hidden = true;
    this.hand.append(this.face, this.waiting);
    const choices = element('div', 'rps-choices');
    for (const [id, label] of [
      ['rock', 'Stein'],
      ['paper', 'Papier'],
      ['scissors', 'Schere'],
    ]) {
      const control = element('button', '', label!);
      const image = art.image(art.icon(`play_rps_${id}`, 64));
      control.prepend(image);
      control.addEventListener('click', () => this.action('choose', id));
      choices.append(control);
      this.choices.push(control);
    }
    this.content.append(choices, element('h3', '', 'Deine Hand'), this.hand);
  }
  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const labels: Record<string, string> = {
      rock: 'Stein',
      paper: 'Papier',
      scissors: 'Schere',
    };
    const value = typeof data.player === 'string' ? data.player : undefined;
    this.face.hidden = !value;
    this.waiting.hidden = !!value;
    if (value) {
      this.face.src = this.art.icon(`play_rps_${value}`);
      this.face.alt = labels[value] ?? value;
    }
    this.status.textContent = data.busy
      ? 'Schere … Stein … Papier …'
      : value
        ? `Deine Hand: ${labels[value]}`
        : 'Wähle deine Hand.';
    for (const control of this.choices) control.disabled = !!data.busy;
  }
}
