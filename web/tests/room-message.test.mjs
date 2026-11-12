import assert from 'node:assert/strict';
import test from 'node:test';
import { RoomMessage } from '../src/ui/RoomMessage.ts';

test('room messages expire five seconds after the most recent message', (t) => {
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'document');
  Object.defineProperty(globalThis, 'document', {
    configurable: true,
    value: { createElement: () => ({ setAttribute() {} }) },
  });
  t.after(() => {
    if (previous) Object.defineProperty(globalThis, 'document', previous);
    else delete globalThis.document;
  });
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const message = new RoomMessage();
  message.show(new Error('Aiko schläft gerade.'));
  t.mock.timers.tick(4000);
  message.show('Aiko ist beschäftigt.');
  t.mock.timers.tick(4999);
  assert.equal(message.element.textContent, 'Aiko ist beschäftigt.');
  t.mock.timers.tick(1);
  assert.equal(message.element.textContent, '');

  message.show('Aiko schläft gerade.');
  message.clear();
  assert.equal(message.element.textContent, '');
});
