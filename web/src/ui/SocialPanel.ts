import { button, element, line } from './dom';
import type { Command } from './dom';

export class SocialPanel {
  readonly element = element('section', 'social-panel');
  constructor(command: Command) {
    this.element.append(
      button('Plaudern', () => {
        void command('care', { action: 'talk' });
      }),
      button('Sprüche und Zitate', () => {
        void command('social', { category: 'single' });
      }),
      button('Witze', () => {
        void command('social', { category: 'twopart' });
      }),
      button('Kuriose Fakten', () => {
        void command('social', { category: 'fact' });
      }),
      button('Horoskopbuch anbieten', () => {
        void command('horoscope');
      }),
      line(
        'Plaudern und das Horoskop funktionieren offline. Neue Online-Inhalte benötigen deine Freigabe in den Einstellungen.',
      ),
    );
  }
}
