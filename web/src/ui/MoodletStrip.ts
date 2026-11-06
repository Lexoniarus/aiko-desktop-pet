import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomArtwork } from './RoomArtwork';
import { element, line } from './dom';

interface Moodlet {
  label: string; description: string;
  value: {instance_id: number; definition_id: string; polarity: string;
    remaining_decay_seconds: number; decay_paused: boolean};
}
export class MoodletStrip {
  readonly element = element('section', 'moodlet-strip');
  private entries = new Map<number, {detail: HTMLDetailsElement; text: HTMLElement}>();
  private empty = line('Gerade wirken keine Moodlets.');
  constructor(private artwork: RoomArtwork) {
    this.element.setAttribute('aria-label', 'Was Aikos Stimmung beeinflusst');
    this.element.append(this.empty);
  }
  update(snapshot: RoomSnapshot): void {
    const status = snapshot.catalog.status as {emotional: {moodlets: Moodlet[]}};
    const icons = snapshot.catalog.moodlet_icons as Record<string, string>;
    const descriptions = snapshot.catalog.moodlet_descriptions as Record<string, string>;
    const values = status.emotional.moodlets;
    this.empty.hidden = values.length > 0;
    const ids = new Set(values.map(m => m.value.instance_id));
    for (const [id, entry] of this.entries) if (!ids.has(id)) {
      entry.detail.remove(); this.entries.delete(id);
    }
    for (const moodlet of values) {
      const id = moodlet.value.instance_id;
      let entry = this.entries.get(id);
      if (!entry) {
        const detail = element('details', `moodlet ${moodlet.value.polarity}`);
        const summary = element('summary');
        summary.setAttribute('aria-label', moodlet.label); summary.title = moodlet.label;
        summary.append(this.artwork.image(this.artwork.icon(icons[moodlet.value.definition_id] ?? 'detail_wellbeing', 64), moodlet.label));
        const text = line(''); detail.append(summary, text); this.element.append(detail);
        entry = {detail, text}; this.entries.set(id, entry);
      }
      entry.text.textContent = descriptions[String(id)] ?? moodlet.description;
    }
  }
}
