import type { RoomSnapshot } from '../bridge/RoomClient';
import { element, line } from './dom';
import { MoodletStrip } from './MoodletStrip';
import type { RoomArtwork } from './RoomArtwork';

const labels: Record<string, string> = {
  satiety: 'Sättigung',
  energy: 'Energie',
  fun: 'Spaß',
  social: 'Geselligkeit',
  affection: 'Zuneigung',
  mood: 'Stimmung',
  friendship: 'Freundschaft',
};
const fields = [
  'relationship_line',
  'wellbeing_line',
  'sleep_context_line',
  'contact_line',
  'hint',
  'objects_line',
  'today',
  'next_event',
];
export class StatusPanel {
  readonly element = element('section');
  private needs = new Map<string, { label: Text; meter: HTMLMeterElement }>();
  private lines = new Map<string, HTMLElement>();
  private emotion = element('h3');
  private moodlets: MoodletStrip;
  constructor(artwork: RoomArtwork) {
    this.moodlets = new MoodletStrip(artwork);
    this.element.classList.add('status-cards');
    this.element.append(this.emotion, this.moodlets.element);
    const needs = element('div', 'needs-grid');
    this.element.append(needs);
    for (const [key, name] of Object.entries(labels)) {
      const row = element('div', 'need-card'),
        label = document.createTextNode(name),
        meter = element('meter');
      meter.min = 0;
      meter.max = 100;
      const icon = key === 'mood' ? 'detail_wellbeing' : `status_${key}`;
      row.append(artwork.image(artwork.icon(icon, 64)), label, meter);
      needs.append(row);
      this.needs.set(key, { label, meter });
    }
    const details = element('details', 'status-details');
    details.append(element('summary', '', 'Alltag und weitere Details'));
    this.element.append(details);
    for (const key of fields) {
      const text = line('');
      this.lines.set(key, text);
      details.append(text);
    }
  }
  update(snapshot: RoomSnapshot): void {
    const status = snapshot.catalog.status as Record<string, unknown>;
    const values = status.status_values as Array<[string, number]>;
    for (const [key, value] of values) {
      const node = this.needs.get(key);
      if (!node) continue;
      node.label.textContent = labels[key] + ' ' + Math.round(value);
      node.meter.value = value;
    }
    for (const [key, node] of this.lines) {
      node.textContent = String(status[key] ?? '');
      node.hidden = !status[key];
    }
    const emotional = status.emotional as {
      state_label: string;
      moodlets: Array<{
        label: string;
        description: string;
        value: { instance_id: number };
      }>;
    };
    this.emotion.textContent = emotional.state_label;
    this.moodlets.update(snapshot);
  }
}
