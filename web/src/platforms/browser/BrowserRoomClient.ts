import type { RoomClient, RoomReply } from '../../bridge/RoomClient';
import type { RoomCommandName } from '../../bridge/commands';

export class BrowserRoomClient implements RoomClient {
  private worker = new Worker(new URL('./python.worker.ts', import.meta.url), {
    type: 'module',
  });
  private sequence = 0;
  private pending = new Map<
    number,
    { resolve: (value: RoomReply) => void; reject: (error: Error) => void }
  >();
  private unlock: (() => void) | undefined;
  private initialized = false;
  private failure: Error | undefined;

  constructor() {
    this.worker.onmessage = (event) => {
      const reply = event.data as RoomReply;
      const pending = this.pending.get(reply.requestId);
      if (!pending) return;
      this.pending.delete(reply.requestId);
      if (reply.ok) pending.resolve(reply);
      else pending.reject(new Error(reply.error ?? 'Aiko meldet einen Fehler.'));
    };
    this.worker.onerror = (event) => {
      this.failure = new Error(event.message);
      for (const pending of this.pending.values()) pending.reject(this.failure);
      this.pending.clear();
    };
  }

  async initialize(root: string): Promise<RoomReply> {
    await new Promise<void>((resolve, reject) => {
      void navigator.locks
        .request('aiko-pet-writer', { ifAvailable: true }, async (lock) => {
          if (!lock) {
            reject(new Error('Aiko ist bereits in einem anderen Fenster geöffnet.'));
            return;
          }
          await new Promise<void>((release) => {
            this.unlock = release;
            resolve();
          });
        })
        .catch(reject);
    });
    const reply = await this.request({ name: 'initialize', root });
    this.initialized = true;
    return reply;
  }

  private request(message: Record<string, unknown>): Promise<RoomReply> {
    if (this.failure) return Promise.reject(this.failure);
    const requestId = ++this.sequence;
    return new Promise((resolve, reject) => {
      this.pending.set(requestId, { resolve, reject });
      this.worker.postMessage({ ...message, requestId });
    });
  }

  command(
    name: RoomCommandName,
    args: Record<string, unknown> = {},
  ): Promise<RoomReply> {
    return this.request({ name, args });
  }

  async close(): Promise<void> {
    try {
      if (this.initialized && !this.failure) await this.command('suspend');
    } finally {
      this.worker.terminate();
      this.unlock?.();
    }
  }
}
