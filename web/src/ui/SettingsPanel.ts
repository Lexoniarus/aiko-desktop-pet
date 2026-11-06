import type { RoomSnapshot } from '../bridge/RoomClient';
import { element, line } from './dom';
import type { Command } from './dom';

export class SettingsPanel {
  readonly element = element('section');
  constructor(snapshot: RoomSnapshot, command: Command) {
    const settings = snapshot.catalog.settings as Record<string, unknown>;
    for (const [key, label] of [
      ['online_social', 'Online-Inhalte erlauben'],
      ['auto_walk', 'Selbstständig umhergehen'],
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
    for (const [key, title, choices] of [
      [
        'ui_scale_percent',
        'Menügröße',
        [75, 100, 125, 150, 175, 200].map((value) => [value, value + ' %']),
      ],
    ] as Array<[string, string, Array<[number, string]>]>) {
      const select = element('select');
      select.setAttribute('aria-label', title);
      for (const [value, label] of choices) {
        const option = element('option', '', label);
        option.value = String(value);
        select.append(option);
      }
      select.value = String(settings[key]);
      select.addEventListener('change', () => {
        void command('settings', { [key]: Number(select.value) });
      });
      const row = element('label', 'setting-row', title);
      row.append(select);
      this.element.append(row);
    }
  }
}
