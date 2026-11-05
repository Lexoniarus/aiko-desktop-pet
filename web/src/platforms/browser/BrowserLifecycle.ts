import type { RoomClient, RoomReply } from '../../bridge/RoomClient';

export class BrowserLifecycle {
  private stopped = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private paused = document.hidden;
  constructor(
    private client: RoomClient,
    private receive: (reply: RoomReply) => Promise<void>,
    private error: (error: unknown) => void,
  ) {
    document.addEventListener('visibilitychange', this.visibility);
    window.addEventListener('pagehide', this.hide);
    window.addEventListener('pageshow', this.show);
  }
  start(): void {
    this.stopped = false;
    void this.tick();
  }
  private tick = async (): Promise<void> => {
    if (this.stopped || this.paused) return;
    try {
      const reply = await this.client.command('tick');
      if (!this.stopped) await this.receive(reply);
    } catch (error) {
      if (!this.stopped) this.error(error);
    }
    if (!this.stopped && !this.paused)
      this.timer = setTimeout(() => {
        void this.tick();
      }, 50);
  };
  private visibility = (): void => {
    if (document.hidden) this.hide();
    else this.show();
  };
  private hide = (): void => {
    if (this.paused || this.stopped) return;
    this.paused = true;
    clearTimeout(this.timer);
    void this.client.command('suspend').then(this.receive).catch(this.error);
  };
  private show = (): void => {
    if (!this.paused || this.stopped) return;
    this.paused = false;
    void this.client
      .command('resume')
      .then(this.receive)
      .then(() => this.tick())
      .catch(this.error);
  };
  stop(): void {
    this.stopped = true;
    clearTimeout(this.timer);
    document.removeEventListener('visibilitychange', this.visibility);
    window.removeEventListener('pagehide', this.hide);
    window.removeEventListener('pageshow', this.show);
  }
}
