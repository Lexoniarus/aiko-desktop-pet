import type { RoomSnapshot } from '../bridge/RoomClient';
import { button, element, line } from './dom';
import type { Command } from './dom';

interface WishCard {
  row: HTMLElement;
  description: HTMLElement;
  pin: HTMLButtonElement;
  pinned: boolean;
}
export class WishPanel {
  readonly element = element('section');
  private empty = line('Aiko hat gerade keinen Wunsch.');
  private cards = new Map<number, WishCard>();
  constructor(private command: Command) {
    this.element.append(this.empty);
  }
  update(snapshot: RoomSnapshot): void {
    const status = snapshot.catalog.status as {
      emotional?: {
        wishes: Array<{
          label: string;
          description: string;
          value: { instance_id: number; pinned: boolean };
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
          pin: button('', () => {
            void this.command('wish_pin', { id, pinned: !entry.pinned });
          }),
        };
        row.append(
          element('h3', '', wish.label),
          description,
          entry.pin,
          button('Verwerfen', () => {
            void this.command('wish_dismiss', { id });
          }),
        );
        this.cards.set(id, entry);
        this.element.append(row);
        card = entry;
      }
      card.pinned = wish.value.pinned;
      card.pin.textContent = card.pinned ? 'Lösen' : 'Merken';
      card.description.textContent =
        descriptions?.[String(id)]?.split('\n').slice(1).join('\n') ?? wish.description;
    }
  }
}
