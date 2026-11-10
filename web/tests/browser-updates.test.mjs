import assert from 'node:assert/strict';
import test from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { BrowserUpdates } from '../src/platforms/browser/BrowserUpdates.ts';
import { browserRuntimeUpdates } from '../src/platforms/browser/BrowserRuntimeUpdates.ts';

function environment(t, response = async () => new Response(null, { status: 404 })) {
  let now = 1_000_000;
  const requests = [];
  const document = Object.assign(new EventTarget(), { hidden: false });
  const window = new EventTarget();
  // Only the empty pending-package lookup is needed; no real save or network.
  const success = (result) => {
    const request = { result };
    queueMicrotask(() => request.onsuccess());
    return request;
  };
  const replacements = {
    document,
    window,
    location: { href: 'https://example.test/room/' },
    indexedDB: {
      open: () =>
        success({
          transaction: () => ({
            objectStore: () => ({ get: () => success(undefined) }),
          }),
          close() {},
        }),
    },
  };
  for (const [name, value] of Object.entries(replacements)) {
    const previous = Object.getOwnPropertyDescriptor(globalThis, name);
    Object.defineProperty(globalThis, name, { configurable: true, value });
    t.after(() => {
      if (previous) Object.defineProperty(globalThis, name, previous);
      else delete globalThis[name];
    });
  }
  t.mock.method(Date, 'now', () => now);
  t.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(String(url), 'https://example.test/room/install.json');
    requests.push(now);
    return response();
  });
  return {
    requests,
    advance: (ms) => {
      now += ms;
    },
    hidden: (value) => {
      document.hidden = value;
    },
    foreground: () => document.dispatchEvent(new Event('visibilitychange')),
    online: () => window.dispatchEvent(new Event('online')),
  };
}

test('startup and foreground/reconnect bursts share a 60-second limit without polling', async (t) => {
  const env = environment(t);
  new BrowserUpdates('installed').start();
  await setImmediate();
  assert.equal(env.requests.length, 1);
  env.advance(59_999);
  for (let i = 0; i < 20; i++) {
    env.foreground();
    env.online();
  }
  await setImmediate();
  assert.equal(env.requests.length, 1);
  env.advance(1);
  env.online();
  env.foreground();
  await setImmediate();
  assert.deepEqual(env.requests, [1_000_000, 1_060_000]);
  env.advance(600_000);
  await setImmediate();
  assert.equal(env.requests.length, 2, 'time passing alone must not trigger a check');
  env.hidden(true);
  env.online();
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 2);
  env.hidden(false);
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 3);
});

test('cached starter event wiring cannot bypass the runtime limit; Settings remains manual', async (t) => {
  const env = environment(t);
  const starter = new BrowserUpdates('cached');
  const runtime = browserRuntimeUpdates(starter.host, 'installed', 100);
  // Historical cached starter: its private timestamp stays zero when check()
  // is delegated. Reproduce its actual event wiring, not the repaired start().
  const cachedLastCheck = 0;
  const cachedEvent = () => {
    if (!document.hidden && Date.now() - cachedLastCheck > 60000) void starter.check();
  };
  document.addEventListener('visibilitychange', cachedEvent);
  window.addEventListener('online', cachedEvent);
  await starter.check();
  env.advance(59_999);
  env.online();
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 1);
  env.advance(1);
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 2);
  env.advance(1);
  await runtime.updates.check();
  assert.equal(env.requests.length, 3, 'explicit Settings check must be immediate');
  env.advance(59_999);
  env.online();
  await setImmediate();
  assert.equal(
    env.requests.length,
    3,
    'manual check also resets the automatic interval',
  );
  env.advance(1);
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 4);
});

test('runtime without a cached starter also enforces the automatic interval', async (t) => {
  const env = environment(t);
  browserRuntimeUpdates(undefined, 'installed', 100);
  await setImmediate();
  env.advance(1);
  env.online();
  await setImmediate();
  assert.equal(env.requests.length, 1);
  env.advance(59_999);
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 2);
});

test('failed checks are throttled too and do not retry on a timer', async (t) => {
  const env = environment(t, async () => {
    throw new Error('Network unavailable');
  });
  const updates = new BrowserUpdates('installed');
  let phase;
  updates.subscribe((state) => {
    phase = state.phase;
  });
  updates.start();
  await setImmediate();
  assert.equal(phase, 'error');
  env.advance(59_999);
  env.online();
  env.foreground();
  await setImmediate();
  assert.equal(env.requests.length, 1);
  env.advance(1);
  env.online();
  await setImmediate();
  assert.equal(env.requests.length, 2);
});

test('an in-flight check is shared even after the interval or a manual request', async (t) => {
  const deferred = Promise.withResolvers();
  const env = environment(t, () => deferred.promise);
  const starter = new BrowserUpdates('cached');
  const runtime = browserRuntimeUpdates(starter.host, 'installed', 100);
  const first = starter.check();
  await setImmediate();
  env.advance(60_000);
  const automatic = starter.check();
  const manual = runtime.updates.check();
  assert.equal(automatic, first);
  assert.equal(manual, first);
  await setImmediate();
  assert.equal(env.requests.length, 1);
  deferred.resolve(new Response(null, { status: 404 }));
  await Promise.all([first, automatic, manual]);
});
