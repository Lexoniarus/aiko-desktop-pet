import type { RoomSnapshot } from '../bridge/RoomClient';
import { element, line } from './dom';
import type { Command } from './dom';

export class SettingsPanel {
  readonly element = element('section');
  constructor(snapshot: RoomSnapshot, command: Command) {
    const settings = snapshot.catalog.settings as Record<string, unknown>;
    for (const [key, label] of [
      ['online_social', 'Online-Inhalte erlauben'],
      ['auto_routine', 'Eigener Tagesrhythmus'],
      ['spontaneous_talk', 'Spontane Kommentare'],
    ] as const) {
      const row = element('label', 'setting-row', label),
        input = element('input');
      input.type = 'checkbox';
      input.checked = !!settings[key];
      input.addEventListener('change', () => {
        void command('settings', { [key]: input.checked });
      });
      row.prepend(input);
      this.element.append(row);
    }
    const zodiac = element('select');
    zodiac.setAttribute('aria-label', 'Sternzeichen');
    const signs = [
      ['', 'Bitte wählen'],
      ['aries', 'Widder'],
      ['taurus', 'Stier'],
      ['gemini', 'Zwillinge'],
      ['cancer', 'Krebs'],
      ['leo', 'Löwe'],
      ['virgo', 'Jungfrau'],
      ['libra', 'Waage'],
      ['scorpio', 'Skorpion'],
      ['sagittarius', 'Schütze'],
      ['capricorn', 'Steinbock'],
      ['aquarius', 'Wassermann'],
      ['pisces', 'Fische'],
    ];
    for (const [value, label] of signs) {
      const option = element('option', '', label!);
      option.value = value!;
      zodiac.append(option);
    }
    zodiac.value = String(settings.zodiac_sign ?? '');
    zodiac.addEventListener('change', () => {
      void command('settings', { zodiac_sign: zodiac.value || null });
    });
    this.element.append(
      element('label', '', 'Sternzeichen'),
      zodiac,
      line(
        'Aikos feste Nachtruhe: 23:00–08:00 Uhr. Dein Tagesrhythmus wird hier nicht gelernt.',
      ),
    );
  }
}
