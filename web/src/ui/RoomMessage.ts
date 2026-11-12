import { element } from './dom.ts';

export class RoomMessage {
  readonly element = element('div', 'room-message');
  private timeout?: ReturnType<typeof setTimeout>;

  constructor() {
    this.element.setAttribute('role', 'status');
  }

  show(error: unknown): void {
    clearTimeout(this.timeout);
    this.element.textContent = error instanceof Error ? error.message : String(error);
    this.timeout = setTimeout(() => this.clear(), 5000);
  }

  clear(): void {
    clearTimeout(this.timeout);
    this.timeout = undefined;
    this.element.textContent = '';
  }
}
