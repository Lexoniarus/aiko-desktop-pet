import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import type { PetScreenBounds } from '../room/AikoView';
import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import type { RoomArtwork } from '../ui/RoomArtwork';
import { record, values } from './GameView';

type Point = { x: number; y: number };

/** Character-side game artwork, separate from speech and from World objects. */
export class GameProps {
  private root = element('section', 'pet-game-props');
  private rps = element('div', 'pet-rps-hand');
  private hand: HTMLImageElement;
  private dealer = element('div', 'bj-dealer');
  private deck: HTMLButtonElement;
  private safe = element('div', 'mm-safe');
  private safeImage: HTMLImageElement;
  private snack: HTMLImageElement;
  private lights = element('div', 'mm-safe-lights');
  private pile: HTMLImageElement;
  private flight = element('div', 'game-flight');
  private game?: Record<string, unknown>;
  private received = 0;
  private motionKey = '';
  private motionImages: HTMLImageElement[] = [];
  private gathered: DOMRect[] = [];
  private handSignature = '';

  constructor(
    private host: HTMLElement,
    room: RoomView,
    private art: RoomArtwork,
    command: Command,
  ) {
    this.root.setAttribute('aria-label', 'Aikos Spielgegenstände');
    this.hand = art.image('', '');
    this.rps.append(element('small', '', 'Aikos Hand'), this.hand);
    this.deck = button('', () => {
      void command('game_action', { action: 'hit' });
    });
    this.deck.className = 'bj-deck';
    this.deck.setAttribute('aria-label', 'Noch eine Karte ziehen');
    this.deck.append(
      art.image(art.file('playing_cards/card_back.png'), 'Kartenstapel'),
    );
    this.safeImage = art.image(art.game('mm-safe/00'), 'Aikos Snack-Tresor');
    this.snack = art.image(art.game('mm-donut'), 'Donut', 'mm-safe-snack');
    this.safe.append(this.safeImage, this.snack, this.lights);
    this.pile = art.image(art.game('c4-pile'), 'Aikos Spielsteine', 'pet-c4-pile');
    this.root.append(
      this.rps,
      this.dealer,
      this.deck,
      this.safe,
      this.pile,
      this.flight,
    );
    host.append(this.root);
    room.followPet((bounds) => this.draw(bounds));
  }

  update(snapshot: RoomSnapshot): void {
    const previous = this.game?.id;
    this.game = snapshot.game ?? undefined;
    this.received = performance.now();
    if (previous !== this.game?.id) {
      this.handSignature = '';
      this.motionKey = '';
      this.motionImages = [];
      this.flight.replaceChildren();
      if (this.game?.id === 'mastermind')
        for (let i = 0; i <= 32; i++) {
          const image = new Image();
          image.src = this.art.game(`mm-safe/${String(i).padStart(2, '0')}`);
        }
    }
    const game = this.game;
    this.rps.hidden =
      game?.id !== 'rock_paper_scissors' || typeof game.aiko !== 'string';
    if (!this.rps.hidden) {
      const move = String(game!.aiko),
        labels: Record<string, string> = {
          rock: 'Stein',
          paper: 'Papier',
          scissors: 'Schere',
        };
      this.hand.src = this.art.icon(`play_rps_${move}`);
      this.hand.alt = labels[move] ?? move;
    }
    this.dealer.hidden = this.deck.hidden = game?.id !== 'blackjack';
    if (!this.dealer.hidden) {
      const cards = values(record(game!.hand).cards),
        signature = JSON.stringify(cards);
      if (signature !== this.handSignature) {
        this.handSignature = signature;
        this.dealer.replaceChildren(element('strong', '', 'Aikos Karten'));
        for (const [index, value] of cards.entries()) {
          const card = record(value);
          const image = this.art.image(
            this.card(value),
            value ? `${card.rank} ${card.suit}` : 'Verdeckte Karte',
          );
          image.dataset.dealerIndex = String(index);
          image.style.setProperty('--card-index', String(index));
          this.dealer.append(image);
        }
        this.dealer.style.setProperty(
          '--card-count',
          String(Math.max(1, cards.length)),
        );
      }
      this.deck.disabled = !!game!.busy || record(game!.table).phase !== 'player';
      this.dealer.classList.toggle('flipping', !!game!.flip);
    }
    this.safe.hidden = game?.id !== 'mastermind';
    if (!this.safe.hidden) {
      const props = record(game!.props),
        frame = Number(props.safe_frame ?? 0);
      this.safeImage.src = this.art.game(`mm-safe/${String(frame).padStart(2, '0')}`);
      this.snack.hidden = !props.snack;
      this.lights.hidden = frame !== 0;
      this.lights.replaceChildren();
      for (const color of values(record(game!.code).slots)) {
        const light = element('i');
        light.dataset.color = String(color ?? '');
        this.lights.append(light);
      }
    }
    this.pile.hidden = game?.id !== 'connect_four';
    this.host.dataset.gameMotion = String(
      record(record(game?.props).motion).kind ?? '',
    );
  }

  private card(value: unknown): string {
    const card = record(value);
    return this.art.file(
      `playing_cards/${value ? `card_${card.suit}_${card.rank}.png` : 'card_back.png'}`,
    );
  }

  private place(node: HTMLElement, x: number, y: number, width?: number): void {
    node.style.left = `${x}px`;
    node.style.top = `${y}px`;
    if (width !== undefined) node.style.width = `${width}px`;
  }

  private draw(bounds: PetScreenBounds): void {
    const game = this.game;
    this.root.hidden =
      !game || bounds.x + bounds.width < 0 || bounds.x > this.host.clientWidth;
    if (!game || this.root.hidden) return;
    const right = bounds.x + bounds.width,
      bottom = bounds.y + bounds.height;
    const panel = this.host.querySelector('.room-panel[open]')?.getBoundingClientRect();
    const limit =
      panel && panel.top < bounds.y + bounds.height / 2
        ? panel.left
        : this.host.clientWidth;
    const speech = this.host
      .querySelector<HTMLElement>('.room-speech:not([hidden])')
      ?.getBoundingClientRect();
    const handX = Math.min(
      limit - 126,
      Math.max(right + 10, (speech?.right ?? 0) + 12),
    );
    this.place(this.rps, Math.max(8, handX), Math.max(90, bounds.y - 148), 120);
    const pending = record(record(game.props).motion);
    const count = Math.max(
        values(record(game.hand).cards).length,
        pending.kind === 'dealer' ? Number(pending.index) + 1 : 0,
      ),
      dealerWidth = 96 + Math.max(0, count - 1) * 32;
    this.place(
      this.dealer,
      Math.max(8, bounds.x - dealerWidth - 12),
      Math.min(this.host.clientHeight - 134, bounds.y + bounds.height * 0.35),
      dealerWidth,
    );
    this.place(this.deck, Math.min(limit - 86, right - 20), bounds.y + 45, 80);
    const safeWidth = Math.min(260, Math.max(148, bounds.x - 20));
    this.place(
      this.safe,
      Math.max(8, bounds.x - safeWidth - 12),
      bottom - (safeWidth * 233) / 296,
      safeWidth,
    );
    this.place(
      this.pile,
      bounds.originX + 64 * bounds.scale,
      bounds.originY + 158 * bounds.scale,
      32 * bounds.scale,
    );
    const motion = record(record(game.props).motion),
      key = `${game.id}:${motion.id ?? ''}`;
    if (key !== this.motionKey) {
      this.motionKey = key;
      this.flight.replaceChildren();
      this.motionImages = [];
      this.gathered =
        motion.kind === 'gather'
          ? [
              ...this.host.querySelectorAll(
                '.bj-player img[data-card-index], .bj-dealer img[data-dealer-index]',
              ),
            ].map((node) => node.getBoundingClientRect())
          : [];
      const amount =
        motion.kind === 'shuffle'
          ? 6
          : motion.kind === 'gather'
            ? this.gathered.length
            : motion.kind
              ? 1
              : 0;
      for (let i = 0; i < amount; i++) {
        const image = this.art.image(this.card(null));
        this.motionImages.push(image);
        this.flight.append(image);
      }
    }
    if (!motion.kind) return;
    const duration = Number(motion.duration),
      fraction = Math.min(
        1,
        Number(motion.fraction) + (performance.now() - this.received) / duration,
      );
    const deck = this.deck.getBoundingClientRect(),
      start = { x: deck.left + deck.width / 2, y: deck.top + deck.height / 2 };
    if (motion.kind === 'shuffle') {
      this.motionImages.forEach((image, i) => {
        const spread =
          Math.sin(Math.PI * fraction) * Math.sin(fraction * 6 * Math.PI + i);
        this.place(
          image,
          start.x + spread * 38,
          start.y - Math.abs(spread) * 16 - i,
          96,
        );
      });
    } else if (motion.kind === 'gather') {
      this.motionImages.forEach((image, i) => {
        const from = this.gathered[i]!;
        this.place(
          image,
          from.x + from.width / 2 + (start.x - from.x - from.width / 2) * fraction,
          from.y + from.height / 2 + (start.y - from.y - from.height / 2) * fraction,
          96,
        );
      });
    } else if (motion.kind === 'chip') this.chip(bounds, motion, fraction);
    else {
      const player = this.host.querySelector('.bj-player')?.getBoundingClientRect();
      if (!player) return;
      const index = Number(motion.index),
        dealer = this.dealer.getBoundingClientRect();
      const placeholder = this.host
        .querySelector('.bj-card-target')
        ?.getBoundingClientRect();
      const target =
        motion.kind === 'dealer'
          ? { x: dealer.left + 48 + index * 32, y: dealer.top + 72 }
          : placeholder
            ? {
                x: placeholder.left + placeholder.width / 2,
                y: placeholder.top + placeholder.height / 2,
              }
            : {
                x: player.left + 60 + index * 62,
                y: player.top + player.height * 0.55,
              };
      const ease = fraction * fraction * (3 - 2 * fraction),
        image = this.motionImages[0];
      if (!image) return;
      image.src = this.card(fraction >= 0.5 ? motion.card : null);
      const flip = Math.min(7, Math.max(0, Math.floor(((fraction - 0.2) / 0.6) * 8))),
        compression = motion.card ? [1, 2, 4, 8, 8, 4, 2, 1][flip]! : 1;
      const width =
        motion.kind === 'player' && placeholder
          ? 80 + (placeholder.width - 80) * ease
          : 96;
      this.place(
        image,
        start.x + (target.x - start.x) * ease,
        start.y + (target.y - start.y) * ease - 28 * Math.sin(Math.PI * fraction),
        width / compression,
      );
    }
  }

  private chip(
    bounds: PetScreenBounds,
    motion: Record<string, unknown>,
    fraction: number,
  ): void {
    const cell = Number(motion.cell),
      targetCell = this.host.querySelector<HTMLElement>(
        `.c4-cell[data-cell="${cell}"]`,
      ),
      board = this.host.querySelector('.c4-board');
    if (!targetCell || !board) return;
    const targetBox = targetCell.getBoundingClientRect(),
      boardBox = board.getBoundingClientRect();
    const start: Point = {
      x: bounds.originX + 96 * bounds.scale,
      y: bounds.originY + 141 * bounds.scale,
    };
    const target: Point = {
      x: targetBox.left + targetBox.width / 2,
      y: boardBox.top + (92 / 480) * boardBox.height,
    };
    const flightFraction = Number(motion.flight_duration) / Number(motion.duration),
      t = Math.min(1, fraction / flightFraction);
    let height = Math.abs(target.y - start.y) * 0.55 + 60;
    const left = boardBox.left + (100 / 480) * boardBox.width,
      right = boardBox.left + (380 / 480) * boardBox.width,
      top = boardBox.top + (112 / 480) * boardBox.height;
    // Same board-clearance construction as frontend.view_models.chip_flight.
    if (start.x < left || start.x > right)
      for (let i = 1; i < 100; i++) {
        const p = i / 100,
          x = start.x + (target.x - start.x) * p,
          size = 32 + (targetBox.width * 0.8 - 32) * p;
        if (x + size / 2 >= left && x - size / 2 <= right)
          height = Math.max(
            height,
            (start.y + (target.y - start.y) * p + size / 2 - top + 14 * (1 - p)) /
              (4 * p * (1 - p)),
          );
      }
    const drop = Math.max(0, (fraction - flightFraction) / (1 - flightFraction));
    const x = start.x + (target.x - start.x) * t,
      y =
        fraction < flightFraction
          ? start.y + (target.y - start.y) * t - 4 * height * t * (1 - t)
          : target.y + (targetBox.top + targetBox.height / 2 - target.y) * drop * drop;
    const image = this.motionImages[0];
    if (!image) return;
    image.hidden = fraction >= flightFraction;
    const falling = board.querySelector<HTMLImageElement>('.c4-falling');
    if (falling && fraction >= flightFraction) {
      falling.hidden = false;
      falling.src = this.art.game('c4-red');
      falling.style.left = `${((x - boardBox.left) / boardBox.width) * 100}%`;
      falling.style.top = `${((y - boardBox.top) / boardBox.height) * 100}%`;
    }
    image.src = this.art.game('c4-red');
    this.place(image, x, y, targetBox.width * 0.8);
  }
}
