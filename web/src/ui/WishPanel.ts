import type { RoomArtwork } from './RoomArtwork';
import type { RoomView } from '../room/RoomView';
import type { RoomSnapshot } from '../bridge/RoomClient';
import { button, element, line } from './dom';
import type { Command } from './dom';

interface WishCard {
  row: HTMLElement;
  description: HTMLElement;
  pin: HTMLButtonElement;
  pinned: boolean;
  progress: HTMLProgressElement;
  target: HTMLElement;
  timer: HTMLElement;
  score: HTMLElement;
}
export class WishPanel {
  readonly element = element('section');
  private empty = line('Aiko hat gerade keinen Wunsch.');
  private cards = new Map<number, WishCard>();
  constructor(private command: Command, private artwork: RoomArtwork, private room: RoomView) {
    this.element.append(this.empty);
  }
  update(snapshot: RoomSnapshot): void {
    const status = snapshot.catalog.status as {
      emotional?: {
        wishes: Array<{
          label: string;
          description: string;
          target_label: string; restriction_label: string;
          value: { instance_id: number; pinned: boolean; area: string; target_id: string;
            remaining_seconds: number; target?: {mode: string};
            goal?: {objective: string; required_count: number};
            game?: {completed_rounds: number; required_count: number; wins: number; losses: number} };
        }>;
      };
    };
    const descriptions = snapshot.catalog.wish_descriptions as Record<string, string>;
    const wishes = status.emotional?.wishes ?? [];
    this.empty.hidden = wishes.length > 0;
    const ids = new Set(wishes.map((wish) => wish.value.instance_id));
    for (const [id, card] of this.cards)
      if (!ids.has(id)) {
        card.row.remove();
        this.cards.delete(id);
      }
    for (const wish of wishes) {
      const id = wish.value.instance_id;
      let card = this.cards.get(id);
      if (!card) {
        const row = element('article', 'wish');
        const description = line('');
        const entry: WishCard = {
          row,
          description,
          pinned: wish.value.pinned,
          progress: element('progress'), target: line(''), timer: line(''), score: line(''),
          pin: button('', () => {
            void this.command('wish_pin', { id, pinned: !entry.pinned });
          }),
        };
        const icon = wish.value.area==='food' ? 'status_satiety' : wish.value.area==='games' ? 'status_fun' : wish.value.area==='affection' ? 'status_affection' : 'status_social';
        const asset = wish.value.target?.mode==='exact' ? this.room.assets.items[wish.value.target_id] : undefined;
        const source = asset ? new URL(asset.file, this.room.root).href : this.artwork.icon(icon,64);
        const heading = element('div', 'wish-heading');
        heading.append(this.artwork.image(source), element('h3', '', wish.label));
        const details = element('details');
        details.append(element('summary', '', 'Zum Wunsch'), description);
        const actions = element('div', 'wish-actions');
        actions.append(entry.pin, button('Verwerfen', () => { void this.command('wish_dismiss', {id}); }));
        row.append(heading, entry.target, entry.progress, entry.score, entry.timer, details, actions);
        this.cards.set(id, entry);
        this.element.append(row);
        card = entry;
      }
      card.target.textContent = [wish.target_label, wish.restriction_label].filter(Boolean).join(' · ');
      const game = wish.value.game;
      card.progress.hidden = !game;
      card.score.hidden = !game;
      if (game) {
        const objective = wish.value.goal?.objective ?? 'total_rounds';
        const wins = ['total_wins', 'retry_win', 'next_win'].includes(objective);
        card.progress.max = wish.value.goal?.required_count ?? game.required_count;
        card.progress.value = wins ? game.wins : game.completed_rounds;
        card.progress.setAttribute('aria-label', `${card.progress.value} von ${card.progress.max}`);
        card.score.textContent = `${game.completed_rounds} Runden · ${game.wins} gewonnen · ${game.losses} verloren`;
      }
      card.timer.textContent = wish.value.pinned ? 'Gemerkt · bleibt erhalten' : `Noch ${Math.max(1, Math.ceil(wish.value.remaining_seconds/60))} Min.`;
      card.row.classList.toggle('pinned', wish.value.pinned);
      card.pinned = wish.value.pinned;
      card.pin.textContent = card.pinned ? 'LÃ¶sen' : 'Merken';
      card.description.textContent =
        descriptions?.[String(id)]?.split('\n').slice(1).join('\n') ?? wish.description;
    }
  }
}
