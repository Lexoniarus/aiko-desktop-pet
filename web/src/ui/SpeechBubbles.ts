import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import { button, element } from './dom';
import type { Command } from './dom';
import { connectFourGeometry } from '../games/ConnectFourGeometry';

type Bounds = { x: number; y: number; width: number; height: number };

export class SpeechBubbles {
  readonly element = element('div', 'room-speech');
  private text = element('p');
  private emote = element('img', 'speech-emote');
  private accent = element('span', 'speech-accent');
  private next = button('Weiter', () => {
    void this.command('speech_next');
  });
  private speech?: RoomSnapshot['speech'];
  private shown = -1;
  private scale = 1;
  private tableGame = false;

  constructor(
    private host: HTMLElement,
    private room: RoomView,
    private command: Command,
  ) {
    this.element.setAttribute('aria-live', 'polite');
    this.element.append(this.emote, this.accent, this.text, this.next);
    this.accent.style.fontSize = '24px';
    this.accent.setAttribute('aria-label', 'Aiko untersucht den Gegenstand');
    this.emote.alt = 'Aikos Reaktion';
    this.emote.draggable = false;
    this.element.hidden = true;
    host.append(this.element);
    room.followPet((bounds) => this.position(bounds));
  }

  update(snapshot: RoomSnapshot): void {
    const speech = (this.speech = snapshot.speech);
    const settings = snapshot.catalog.settings as Record<string, unknown>;
    this.scale = Number(settings.ui_scale_percent ?? 100) / 100;
    this.tableGame = snapshot.game?.id === 'connect_four';
    if (this.tableGame) this.scale = Math.min(this.scale, 1.25);
    this.element.style.zoom = this.tableGame ? String(this.scale) : '';
    this.text.textContent = speech.text;
    this.text.hidden = !speech.text;
    this.accent.textContent = speech.accent ?? '';
    this.accent.hidden = !speech.accent;
    this.next.hidden = !speech.story;
    this.emote.hidden = !speech.emote;
    this.element.classList.toggle('emote-only', !!speech.emote && !speech.text);
    if (speech.emote)
      this.emote.src = new URL(
        `assets/emotes/emote_${speech.emote}.png`,
        this.room.root,
      ).href;
  }

  private position(bounds: Bounds): void {
    const speech = this.speech;
    const content = !!speech && (!!speech.text || !!speech.emote || !!speech.accent);
    const visible =
      this.room.petVisible &&
      bounds.x + bounds.width > 0 &&
      bounds.x < this.host.clientWidth &&
      bounds.y < this.host.clientHeight &&
      bounds.y + bounds.height > 0;
    this.element.hidden = !content || (!visible && !this.tableGame);
    if (this.element.hidden) return;
    const panel = this.host
      .querySelector<HTMLDialogElement>('.room-panel[open]')
      ?.getBoundingClientRect();
    const hand = this.host.querySelector<HTMLElement>('.pet-rps-hand:not([hidden])');
    const sidePanel = panel && panel.top < bounds.y + bounds.height / 2;
    const reserve = hand ? hand.getBoundingClientRect().width + 12 : 0;
    const center = bounds.x + bounds.width / 2;
    const sceneBottom = this.room.camera.sceneHeight;
    const besideAiko =
      center > this.host.clientWidth / 2
        ? this.host.clientWidth - bounds.x - bounds.width - 16
        : bounds.x - 16;
    const available =
      panel && sidePanel && !this.tableGame
        ? panel.left - reserve - 24
        : this.tableGame && visible && sceneBottom < 440 && besideAiko >= 140
          ? besideAiko
          : this.host.clientWidth - 16;
    if (!this.element.classList.contains('emote-only'))
      this.element.style.width = `${Math.max(96, Math.min(280, available / this.scale))}px`;
    else this.element.style.removeProperty('width');
    const rect = this.element.getBoundingClientRect();
    let x = center - rect.width / 2;
    let y = bounds.y - rect.height - 8;
    const top = 8;
    if (y < top) {
      y = Math.max(top, bounds.y + 4);
      x = bounds.x + bounds.width + 8;
      if (x + rect.width > this.host.clientWidth - 8) x = bounds.x - rect.width - 8;
    }
    const table = this.tableGame && this.room.tableGameFrame();
    if (table) {
      const boardRight = table.x + connectFourGeometry.size * table.scale;
      const boardTop = table.y + connectFourGeometry.artTop * table.scale;
      const boardBottom = table.y + connectFourGeometry.artBottom * table.scale;
      const aboveBoard = boardTop - rect.height - 12;
      const left = 8;
      const right = this.host.clientWidth - rect.width - 8;
      const bottom = sceneBottom - rect.height - 14;
      const onRight = center > (table.x + boardRight) / 2;
      const besideRight =
        Math.max(boardRight, visible ? bounds.x + bounds.width : boardRight) + 8;
      const besideLeft =
        Math.min(table.x, visible ? bounds.x : table.x) - rect.width - 8;
      const sideX = onRight ? besideRight : besideLeft;
      const oppositeX = onRight ? besideLeft : besideRight;
      const anchorX = Math.max(
        left,
        Math.min(right, visible ? x : onRight ? right : left),
      );
      const candidates = [
        { x: anchorX, y: Math.min(visible ? y : aboveBoard, aboveBoard) },
        { x: anchorX, y: aboveBoard },
        { x: sideX, y: Math.max(top, Math.min(y, bottom)) },
        { x: oppositeX, y: Math.max(top, Math.min(y, bottom)) },
        { x: anchorX, y: boardBottom + 8 },
      ];
      const position = candidates.find(
        (candidate) =>
          candidate.x >= left &&
          candidate.x <= right &&
          candidate.y >= top &&
          candidate.y <= bottom &&
          (!visible ||
            candidate.x + rect.width <= bounds.x ||
            candidate.x >= bounds.x + bounds.width ||
            candidate.y + rect.height <= bounds.y ||
            candidate.y >= bounds.y + bounds.height) &&
          (!panel ||
            candidate.x + rect.width <= panel.left ||
            candidate.x >= panel.right ||
            candidate.y + rect.height <= panel.top ||
            candidate.y >= panel.bottom),
      );
      x = position?.x ?? anchorX;
      y = position?.y ?? aboveBoard;
    }
    if (panel && sidePanel && reserve && x + rect.width + reserve > panel.left - 12)
      x = panel.left - rect.width - reserve - 12;
    if (
      panel &&
      x + rect.width > panel.left &&
      x < panel.right &&
      y + rect.height > panel.top &&
      y < panel.bottom &&
      panel.left - rect.width - 12 >= 8
    )
      x = panel.left - rect.width - 12;
    x = Math.max(8, Math.min(x, this.host.clientWidth - rect.width - 8));
    y = Math.max(top, Math.min(y, sceneBottom - rect.height - 14));
    this.element.style.left = `${x / this.scale}px`;
    this.element.style.top = `${y / this.scale}px`;
    this.element.style.setProperty(
      '--tail-x',
      `${Math.max(12, Math.min(rect.width - 12, center - x)) / this.scale}px`,
    );
    if (speech?.text && speech.id !== this.shown && !document.hidden) {
      this.shown = speech.id;
      void this.command('speech_ack', { id: speech.id });
    }
  }
}
