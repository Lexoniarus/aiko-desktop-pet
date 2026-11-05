import type { RoomClient, RoomReply } from '../../bridge/RoomClient';
import type { RoomCommandName } from '../../bridge/commands';

export class BrowserRoomClient implements RoomClient {
  private worker = new Worker(new URL('./python.worker.ts', import.meta.url), { type: 'module' });
  private sequence = 0;
  private pending = new Map<number, { resolve: (value: RoomReply) => void; reject: (error: Error) => void }>();
  private unlock: (() => void) | undefined;

  constructor() {
    this.worker.onmessage = event => {
      const reply = event.data as RoomReply;
      const pending = this.pending.get(reply.requestId);
      if (!pending) return;
      this.pending.delete(reply.requestId);
      if (reply.ok) pending.resolve(reply);
      else pending.reject(new Error(reply.error ?? 'Aiko meldet einen Fehler.'));
    };
    this.worker.onerror = event => {
      for (const pending of this.pending.values()) pending.reject(new Error(event.message));
      this.pending.clear();
    };
  }

  async initialize(root: string): Promise<RoomReply> {
    await new Promise<void>((resolve, reject) => {
      void navigator.locks.request('aiko-pet-writer', { ifAvailable: true }, async lock => {
        if (!lock) { reject(new Error('Aiko ist bereits in einem anderen Fenster geöffnet.')); return; }
        await new Promise<void>(release => { this.unlock = release; resolve(); });
      }).catch(reject);
    });
    return this.request({ name: 'initialize', root });
  }

  private request(message: Record<string, unknown>): Promise<RoomReply> {
    const requestId = ++this.sequence;
    return new Promise((resolve, reject) => {
      this.pending.set(requestId, { resolve, reject });
      this.worker.postMessage({ ...message, requestId });
    });
  }

  command(name: RoomCommandName, args: Record<string, unknown> = {}): Promise<RoomReply> {
    return this.request({ name, args });
  }

  async close(): Promise<void> {
    try { await this.command('suspend'); }
    finally { this.worker.terminate(); this.unlock?.(); }
  }
}
