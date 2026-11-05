import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
export interface GameView {
  element: HTMLElement;
  update(data: Record<string, unknown>): void;
  destroy?(): void;
}
export const record = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
export const values = (value: unknown): unknown[] =>
  Array.isArray(value) ? value : [];
export class GameFrame {
  readonly element = element('section', 'game-view');
  readonly content = element('div', 'game-content');
  readonly score = element('p', 'game-score');
  constructor(readonly command: Command) {
    this.element.append(this.score, this.content);
  }
  action(name: string, value?: unknown): void {
    void this.command('game_action', { action: name, value });
  }
  scoreline(value: unknown): void {
    const s = record(value);
    this.score.textContent = `Du ${s.wins ?? 0} · Aiko ${s.losses ?? 0} · Unentschieden ${s.draws ?? 0}`;
  }
  next(): HTMLButtonElement {
    return button('Nächste Runde', () => this.action('next'));
  }
}
