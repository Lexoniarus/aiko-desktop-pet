import type {
  RoomHostOptions,
  RoomUpdates,
  UpdateState,
} from '../../bridge/RoomUpdates';
import { activatePendingPackage, pendingPackage } from './PackageStore';
import type { InstalledPackage } from './PackageStore';
import { publishedPackage, installPublishedPackage } from './PublishedPackage';

export class BrowserUpdates implements RoomUpdates {
  private state: UpdateState;
  private listeners = new Set<(state: UpdateState) => void>();
  private checking?: Promise<void>;
  private lastCheck = 0;
  private shutdown?: () => Promise<void>;
  private gameOpen = false;

  constructor(version: string) {
    this.state = {
      installedVersion: version,
      phase: 'idle',
      message: 'Updates werden beim Öffnen geprüft.',
      canRestart: false,
    };
  }

  readonly host: RoomHostOptions = {
    updates: this,
    registerShutdown: (shutdown) => {
      this.shutdown = shutdown;
      this.publish({});
    },
    setGameOpen: (open) => {
      if (this.gameOpen !== open) {
        this.gameOpen = open;
        this.publish({});
      }
    },
  };

  subscribe(listener: (state: UpdateState) => void): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  private publish(change: Partial<UpdateState>): void {
    this.state = { ...this.state, ...change };
    this.state.canRestart =
      this.state.phase === 'ready' && !!this.shutdown && !this.gameOpen;
    for (const listener of this.listeners) listener(this.state);
  }

  start(): void {
    const check = (): void => {
      if (!document.hidden && Date.now() - this.lastCheck > 60000) void this.check();
    };
    document.addEventListener('visibilitychange', check);
    window.addEventListener('online', check);
    void this.check();
  }

  check(): Promise<void> {
    if (this.state.phase === 'applying') return Promise.resolve();
    if (this.checking) return this.checking;
    this.lastCheck = Date.now();
    this.checking = this.download().finally(() => {
      this.checking = undefined;
    });
    return this.checking;
  }

  private async download(): Promise<void> {
    let pending: InstalledPackage | undefined;
    try {
      pending = await pendingPackage();
      this.publish({ phase: 'checking', message: 'Suche nach Updates …' });
      const published = await publishedPackage();
      if (
        published &&
        published.version !== this.state.installedVersion &&
        published.version !== pending?.version
      ) {
        this.publish({
          phase: 'downloading',
          availableVersion: published.version,
          message: 'Update wird im Hintergrund geladen …',
        });
        pending = await installPublishedPackage(
          published,
          (message) => this.publish({ message }),
          'pending',
        );
      }
      if (!pending) {
        this.publish({
          phase: 'current',
          availableVersion: undefined,
          message: published
            ? 'Aiko ist auf dem aktuellen Stand.'
            : 'Für diese Installation ist kein Online-Update veröffentlicht.',
        });
        return;
      }
    } catch (error) {
      if (!pending) {
        this.publish({
          phase: 'error',
          message: `Update derzeit nicht verfügbar. Aiko läuft weiter. ${error instanceof Error ? error.message : String(error)}`,
        });
        return;
      }
    }
    this.publish({
      phase: 'ready',
      availableVersion: pending.version,
      message: this.shutdown
        ? 'Update bereit. Beim nächsten Start wird es übernommen. Du kannst Aiko auch jetzt neu starten.'
        : 'Update bereit. Bitte Aiko im App-Umschalter vollständig schließen und wieder öffnen.',
    });
  }

  async apply(): Promise<void> {
    if (!this.state.canRestart || !this.shutdown) return;
    this.publish({ phase: 'applying', message: 'Aikos Spielstand wird gesichert …' });
    try {
      await this.shutdown();
    } catch (error) {
      this.publish({
        phase: 'ready',
        message: `Spielstand konnte nicht gesichert werden. Update bleibt bereit. ${error instanceof Error ? error.message : String(error)}`,
      });
      return;
    }
    try {
      if (await activatePendingPackage()) {
        location.reload();
        return;
      }
    } catch {
      /* Keep the verified package for the next cold start. */
    }
    // The old runtime has stopped; keep the notice visible until reopening.
    this.publish({
      phase: 'applying',
      message:
        'Bitte Aiko im App-Umschalter vollständig schließen und wieder öffnen, um das Update zu übernehmen.',
    });
  }
}
