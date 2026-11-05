import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import type { RoomArtwork } from '../ui/RoomArtwork';
import { PointerDrag } from '../input/PointerDrag';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';

const names: Record<string, string> = {
  red: 'Rot',
  yellow: 'Gelb',
  blue: 'Blau',
  green: 'Grün',
  purple: 'Lila',
  white: 'Weiß',
};

export class MastermindView extends GameFrame implements GameView {
  private history = element('div', 'mm-history');
  private code = element('div', 'mm-code');
  private slots = element('div', 'mm-slots');
  private activeRow = element('div', 'mm-active');
  private attempt = element('span');
  private palette = element('div', 'mm-palette');
  private selected: (string | null)[] = [null, null, null, null];
  private active = 0;
  private count = 0;
  private selectedColor?: string;
  private colors: string[] = [];
  private editable = false;
  private submit = button('Prüfen', () => {
    if (!this.submit.disabled) this.action('submit', [...this.selected]);
  });
  private clear = button('Position leeren', () => {
    if (this.editable) {
      this.selected[this.active] = null;
      this.drawSlots();
    }
  });
  private nextButton = this.next();
  private drag = new PointerDrag();
  private ghost?: HTMLImageElement;

  constructor(
    command: Command,
    private art: RoomArtwork,
  ) {
    super(command);
    this.element.dataset.game = 'mastermind';
    this.activeRow.append(this.attempt, this.slots);
    this.content.append(
      element(
        'p',
        '',
        'Knacke Aikos Snack-Tresor: vier Positionen, sechs Farben, zehn Versuche. Farben dürfen mehrfach vorkommen.',
      ),
      this.code,
      this.palette,
      element(
        'p',
        'mm-help',
        'Farbe wählen und eine Position antippen – oder einen Stein hineinziehen. Steine der aktiven Reihe lassen sich vertauschen.',
      ),
      this.activeRow,
      this.submit,
      this.clear,
      this.nextButton,
      this.history,
    );
    window.addEventListener('keydown', this.key);
    this.drawSlots();
  }

  private piece(color: string | null, label = ''): HTMLImageElement {
    return this.art.image(
      color ? this.art.game(`mm-${color}`) : this.art.file('mastermind/black.png'),
      label,
      'mm-piece',
    );
  }

  private bindDrag(control: HTMLElement, color: string, source?: number): void {
    control.addEventListener('pointerdown', (event) => {
      if (!this.editable || event.button !== 0 || !event.isPrimary) return;
      event.preventDefault();
      this.drag.begin(event, {
        start: () => {
          this.ghost = this.piece(color);
          this.ghost.className = 'drag-portion mm-drag-piece';
          document.body.append(this.ghost);
        },
        move: (x, y) => {
          if (this.ghost)
            this.ghost.style.transform = `translate(${x}px,${y}px) translate(-50%,-50%)`;
        },
        finish: (x, y, dragged, cancelled) => {
          this.ghost?.remove();
          this.ghost = undefined;
          if (cancelled || !this.editable) return;
          // The stable capture owner receives pointerup, so dispatch the short
          // tap to its original control explicitly instead of losing the click.
          if (!dragged) {
            control.click();
            return;
          }
          const target = document
            .elementFromPoint(x, y)
            ?.closest<HTMLElement>('[data-mm-slot]');
          if (!target || !this.slots.contains(target)) return;
          const index = Number(target.dataset.mmSlot);
          if (source !== undefined) this.selected[source] = this.selected[index]!;
          this.selected[index] = color;
          this.active = index;
          this.drawSlots();
        },
      });
    });
  }

  private drawSlots(): void {
    this.slots.replaceChildren();
    this.selected.forEach((value, index) => {
      const pin = button('', () => {
        if (!this.editable) return;
        this.active = index;
        if (this.selectedColor) this.selected[index] = this.selectedColor;
        this.drawSlots();
      });
      pin.dataset.mmSlot = String(index);
      pin.dataset.color = value ?? '';
      pin.className = 'mm-pin';
      pin.disabled = !this.editable;
      pin.classList.toggle('selected', this.active === index);
      pin.setAttribute(
        'aria-label',
        `Position ${index + 1}: ${value ? names[value] : 'leer'}`,
      );
      pin.append(this.piece(value));
      if (value) this.bindDrag(pin, value, index);
      this.slots.append(pin);
    });
    this.submit.disabled =
      !this.editable || this.selected.some((value) => value === null);
    this.clear.disabled = !this.editable;
  }

  update(data: Record<string, unknown>): void {
    this.scoreline(data.score);
    const view = record(data.view),
      guesses = values(view.guesses);
    const editable = !data.busy && !view.result;
    if (this.editable && !editable) this.drag.cancel();
    this.editable = editable;
    if (guesses.length !== this.count) {
      this.count = guesses.length;
      this.selected = [null, null, null, null];
      this.active = 0;
    }
    if (!this.palette.children.length) {
      this.colors = values(data.colors).map(String);
      for (const [index, color] of this.colors.entries()) {
        const control = button('', () => {
          if (!this.editable) return;
          this.selectedColor = color;
          for (const button of this.palette.querySelectorAll('button')) {
            button.classList.toggle('selected', button.dataset.color === color);
            button.setAttribute('aria-pressed', String(button.dataset.color === color));
          }
        });
        control.className = 'mm-color';
        control.dataset.color = color;
        control.setAttribute('aria-label', names[color] ?? color);
        control.append(
          this.piece(color),
          element('span', '', `${index + 1}: ${names[color]}`),
        );
        this.bindDrag(control, color);
        this.palette.append(control);
      }
    }
    for (const button of this.palette.querySelectorAll('button'))
      button.disabled = !this.editable;
    this.code.replaceChildren(element('strong', '', 'Aikos Code'));
    for (const [index, color] of values(record(data.code).slots).entries()) {
      const slot = element('span', 'mm-code-slot');
      slot.append(
        color
          ? this.piece(String(color), names[String(color)])
          : element('strong', '', '?'),
        element('small', '', String(index + 1)),
      );
      this.code.append(slot);
    }
    this.history.replaceChildren();
    this.history.hidden = !guesses.length;
    this.activeRow.hidden = !!view.result;
    this.attempt.textContent = `Versuch ${guesses.length + 1}`;
    for (let index = 0; index < guesses.length; index++) {
      const row = element('div', 'mm-guess');
      row.append(element('span', 'mm-row-number', String(index + 1)));
      const guess = record(guesses[index]);
      const pins = element('div', 'mm-row-pins');
      const colors = values(guess.colors);
      for (let i = 0; i < 4; i++) pins.append(this.piece(String(colors[i])));
      row.append(pins);
      const feedback = record(guess.feedback),
        count = index === guesses.length - 1 ? Number(data.feedback_count ?? 0) : 4;
      const pegs = element('span', 'mm-feedback');
      const exact = Number(feedback.exact ?? 0),
        misplaced = Number(feedback.misplaced ?? 0);
      pegs.setAttribute(
        'aria-label',
        guesses[index]
          ? `${Math.min(exact, count)} exakt, ${Math.max(0, Math.min(misplaced, count - exact))} versetzt`
          : 'Noch nicht geprüft',
      );
      for (let i = 0; i < 4; i++) {
        const peg = element('span', 'mm-feedback-peg');
        if (guesses[index] && i < count)
          peg.dataset.kind =
            i < exact ? 'exact' : i < exact + misplaced ? 'misplaced' : 'empty';
        pegs.append(peg);
      }
      row.append(pegs);
      this.history.append(row);
    }
    this.drawSlots();
    this.nextButton.hidden = !view.result;
    this.nextButton.disabled = !!data.busy;
    this.status.textContent = view.result
      ? view.result === 'win'
        ? 'Code geknackt!'
        : 'Aikos Code bleibt dieses Mal sicher.'
      : data.busy
        ? 'Aiko prüft die Steine …'
        : `${10 - guesses.length} Versuche übrig.`;
  }

  private key = (event: KeyboardEvent): void => {
    if (
      !this.editable ||
      !this.element.isConnected ||
      (event.target as HTMLElement)?.matches('input,select,textarea')
    )
      return;
    const color = this.colors[Number(event.key) - 1];
    if (color) {
      this.selected[this.active] = color;
      this.active = (this.active + 1) % 4;
    } else if (event.key === 'ArrowLeft') this.active = (this.active + 3) % 4;
    else if (event.key === 'ArrowRight') this.active = (this.active + 1) % 4;
    else if (event.key === 'Backspace' || event.key === 'Delete')
      this.selected[this.active] = null;
    else if (event.key === 'Enter') {
      if (!this.submit.disabled) this.action('submit', [...this.selected]);
    } else return;
    event.preventDefault();
    this.drawSlots();
  };

  destroy(): void {
    this.drag.cancel();
    this.ghost?.remove();
    window.removeEventListener('keydown', this.key);
  }
}
