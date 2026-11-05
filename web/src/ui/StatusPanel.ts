import type { RoomSnapshot } from '../bridge/RoomClient';
import { element, line } from './dom';

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
  private moodlets = new Map<
    number,
    { detail: HTMLDetailsElement; text: HTMLElement }
  >();
  constructor() {
    for (const [key, name] of Object.entries(labels)) {
      const row = element('label', 'need-row'),
        label = document.createTextNode(name),
        meter = element('meter');
      meter.min = 0;
      meter.max = 100;
      row.append(label, meter);
      this.element.append(row);
      this.needs.set(key, { label, meter });
    }
    for (const key of fields) {
      const text = line('');
      this.lines.set(key, text);
      this.element.append(text);
    }
    this.element.append(this.emotion);
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
    const descriptions = snapshot.catalog.moodlet_descriptions as Record<
      string,
      string
    >;
    const ids = new Set(emotional.moodlets.map((m) => m.value.instance_id));
    for (const [id, node] of this.moodlets)
      if (!ids.has(id)) {
        node.detail.remove();
        this.moodlets.delete(id);
      }
    for (const moodlet of emotional.moodlets) {
      const id = moodlet.value.instance_id;
      let node = this.moodlets.get(id);
      if (!node) {
        const detail = element('details'),
          text = line('');
        detail.append(element('summary', '', moodlet.label), text);
        this.element.append(detail);
        node = { detail, text };
        this.moodlets.set(id, node);
      }
      node.text.textContent = descriptions?.[String(id)] ?? moodlet.description;
    }
  }
}
