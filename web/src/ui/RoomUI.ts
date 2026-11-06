import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import type { ObjectDragController } from '../input/ObjectDragController';
import { FoodPanel } from './FoodPanel';
import { SocialPanel } from './SocialPanel';
import { MoodletStrip } from './MoodletStrip';
import { StatusPanel } from './StatusPanel';
import { WishPanel } from './WishPanel';
import { SettingsPanel } from './SettingsPanel';
import { CreditsPanel } from './CreditsPanel';
import { UpdateControls } from './UpdateControls';
import { SpeechBubbles } from './SpeechBubbles';
import { RoomArtwork } from './RoomArtwork';
import type { RoomUpdates } from '../bridge/RoomUpdates';
import { RockPaperScissorsView } from '../games/RockPaperScissorsView';
import { TicTacToeView } from '../games/TicTacToeView';
import { BlackjackView } from '../games/BlackjackView';
import { ConnectFourView } from '../games/ConnectFourView';
import { MastermindView } from '../games/MastermindView';
import { QuizView } from '../games/QuizView';
import type { GameView } from '../games/GameView';
import { GameProps } from '../games/GameProps';
import { button, element } from './dom';
import type { Command } from './dom';

export class RoomUI {
  private toolbar = element('nav', 'room-toolbar');
  private speech: SpeechBubbles;
  private artwork: RoomArtwork;
  private props: GameProps;
  private moodlets: MoodletStrip;
  private find = button('Aiko finden', () => {
    if (this.room.petPosition) this.room.camera.lookAt(this.room.petPosition);
  });
  private fix = button('Aiko fixieren', () => {
    if (this.room.camera.following) this.room.camera.releaseFollow();
    else this.room.camera.followPet();
  });
  private panel = element('dialog', 'room-panel');
  private panelBody = element('div', 'panel-body');
  private title = element('h2');
  private snapshot?: RoomSnapshot;
  private panelName = '';
  private activePanel: StatusPanel | WishPanel | undefined;
  private game: GameView | undefined;
  private gameId = '';
  private gameSignature = '';
  private updates?: UpdateControls;
  private pet = button('Streicheln', () => {
    void this.command('care', { action: 'pet' });
  });
  private sleep = button('Schlafen', () => {
    void this.command('care', { action: 'sleep' });
  });
  readonly status = element('div', 'room-message');
  constructor(
    private host: HTMLElement,
    private room: RoomView,
    private drag: ObjectDragController,
    private command: Command,
    updates?: RoomUpdates,
  ) {
    this.artwork = new RoomArtwork(room.root, room.assets.ui);
    this.artwork.apply(host);
    this.moodlets = new MoodletStrip(this.artwork);
    this.moodlets.element.classList.add('room-moodlets');
    this.speech = new SpeechBubbles(host, room, command);
    this.props = new GameProps(host, room, this.artwork, command);
    if (updates) this.updates = new UpdateControls(updates);
    this.toolbar.setAttribute('aria-label', 'Aikos Zimmer');
    for (const [name, label] of [
      ['food', 'Füttern'],
      ['games', 'Spielen'],
      ['social', 'Plaudern'],
      ['status', 'Befinden'],
      ['wishes', 'Wünsche'],
      ['settings', 'Einstellungen'],
    ])
      this.toolbar.append(
        button(label!, () => {
          this.open(name!);
        }),
      );
    this.toolbar.prepend(
      button('Aiko rufen', () => {
        void command('call', room.callPoint());
      }),
    );
    this.status.setAttribute('role', 'status');
    const care = element('div', 'quick-care');
    care.append(
      this.pet,
      this.sleep,
      this.find,
      this.fix,
    );
    const header = element('header', 'panel-header');
    header.append(
      this.title,
      button('Schließen', () => {
        this.close();
      }),
    );
    this.panel.append(header, this.panelBody);
    this.panel.setAttribute('aria-label', 'Aikos Zimmermenü');
    this.panel.addEventListener('cancel', (event) => {
      event.preventDefault();
      this.close();
    });
    drag.onDragBegin = () => {
      this.panel.close();
      this.panelName = '';
      this.activePanel = undefined;
    };
    host.append(this.toolbar, care, this.panel, this.status, this.moodlets.element);
    room.followPet(() => {
      this.find.hidden = room.petVisible;
      this.fix.setAttribute('aria-pressed', String(room.camera.following));
      this.fix.textContent = room.camera.following ? 'Fixierung l�sen' : 'Aiko fixieren';
      this.moodlets.element.hidden = this.panel.open;
    });
  }
  private open(name: string): void {
    const snapshot = this.snapshot;
    if (!snapshot) return;
    if (this.gameId && name !== 'games') {
      void this.command('game_close').then(() => this.open(name));
      return;
    }
    this.panelName = name;
    this.activePanel = undefined;
    this.panelBody.replaceChildren();
    const titles: Record<string, string> = {
      food: 'Füttern',
      games: 'Spielen',
      social: 'Plaudern',
      status: 'Befinden',
      wishes: 'Wünsche',
      settings: 'Einstellungen',
      credits: 'Quellen und Bildrechte',
    };
    this.title.textContent = titles[name] ?? name;
    if (name === 'food')
      this.panelBody.append(
        new FoodPanel(snapshot, this.room, this.drag, this.command).element,
      );
    if (name === 'social')
      this.panelBody.append(
        new SocialPanel(async (action, args) => {
          this.close();
          await this.command(action, args);
        }).element,
      );
    if (name === 'status') {
      this.activePanel = new StatusPanel(this.artwork);
      this.activePanel.update(snapshot);
      this.panelBody.append(this.activePanel.element);
    }
    if (name === 'wishes') {
      this.activePanel = new WishPanel(this.command, this.artwork, this.room);
      this.activePanel.update(snapshot);
      this.panelBody.append(this.activePanel.element);
    }
    if (name === 'settings') {
      this.panelBody.append(
        new SettingsPanel(snapshot, this.command).element,
        button('Quellen und Bildrechte', () => this.open('credits')),
        button('Paket aus Datei importieren', () => {
          void this.command('suspend').then(() =>
            location.assign(new URL('./', location.href).href + '?install=1'),
          );
        }),
      );
      if (this.updates) this.panelBody.prepend(this.updates.element);
    }
    if (name === 'credits')
      this.panelBody.append(new CreditsPanel(snapshot, this.room.root).element);
    if (name === 'games') {
      const games = [
        ['rock_paper_scissors', 'Schere–Stein–Papier'],
        ['tic_tac_toe', 'Tic-Tac-Toe'],
        ['blackjack', 'Blackjack'],
        ['connect_four', 'Vier gewinnt'],
        ['mastermind', 'Mastermind'],
        ['quiz', 'Quiz'],
      ];
      if (this.game) {
        this.title.textContent =
          games.find(([id]) => id === this.gameId)?.[1] ?? 'Spielen';
        this.panelBody.append(this.game.element);
      } else {
        const menu = element('div', 'game-menu');
        const icons: Record<string, string> = {
          rock_paper_scissors: this.artwork.icon('game_rps', 64),
          tic_tac_toe: this.artwork.icon('game_tic_tac_toe', 64),
          blackjack: this.artwork.game('blackjack-table'),
          connect_four: this.artwork.game('c4-board'),
          mastermind: this.artwork.game('mm-blue'),
          quiz: this.artwork.game('quiz-emblem'),
        };
        for (const [id, label] of games) {
          const control = button(label!, () => {
            void this.command('game_open', { id });
          });
          control.prepend(this.artwork.image(icons[id!]!));
          menu.append(control);
        }
        this.panelBody.append(menu);
      }
    }
    if (!this.panel.open) this.panel.show();
  }
  private close(): void {
    if (this.gameId) void this.command('game_close');
    this.panel.close();
    this.panelName = '';
    this.activePanel = undefined;
  }
  update(snapshot: RoomSnapshot): void {
    this.snapshot = snapshot;
    const settings = snapshot.catalog.settings as Record<string, unknown>;
    this.host.style.setProperty(
      '--ui-scale',
      String((Number(settings.ui_scale_percent) || 100) / 100),
    );
    this.sleep.textContent = snapshot.pet.sleeping ? 'Aufwecken' : 'Schlafen';
    this.pet.disabled = !!snapshot.game;
    this.sleep.disabled = !!snapshot.game;
    this.speech.update(snapshot);
    this.moodlets.update(snapshot);
    this.props.update(snapshot);
    if (this.activePanel) this.activePanel.update(snapshot);
    const id = String(snapshot.game?.id ?? '');
    if (id !== this.gameId) {
      this.game?.destroy?.();
      this.game = undefined;
      this.gameId = id;
      this.gameSignature = '';
      const types: Record<string, () => GameView> = {
        rock_paper_scissors: () =>
          new RockPaperScissorsView(this.command, this.artwork),
        tic_tac_toe: () => new TicTacToeView(this.command, this.artwork),
        blackjack: () => new BlackjackView(this.command, this.artwork),
        connect_four: () => new ConnectFourView(this.command, this.artwork),
        mastermind: () => new MastermindView(this.command, this.artwork),
        quiz: () => new QuizView(this.command, this.artwork),
      };
      if (id && types[id]) {
        this.room.frameForGame();
        this.game = types[id]!();
        this.open('games');
      } else {
        this.room.camera.setGame(false);
        if (this.panelName === 'games') this.open('games');
      }
    }
    this.panel.classList.toggle('game-panel', !!id);
    if (this.game && snapshot.game) {
      const signature = JSON.stringify(snapshot.game);
      if (signature !== this.gameSignature) {
        this.game.update(snapshot.game);
        this.gameSignature = signature;
      }
    }
  }
  message(error: unknown): void {
    this.status.textContent = error instanceof Error ? error.message : String(error);
  }
}
