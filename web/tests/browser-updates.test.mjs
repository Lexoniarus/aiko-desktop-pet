import assert from 'node:assert/strict';
import test from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { BrowserUpdates } from '../src/platforms/browser/BrowserUpdates.ts';
import { browserRuntimeUpdates } from '../src/platforms/browser/BrowserRuntimeUpdates.ts';

function environment(t, response = async () => new Response(null, { status: 404 })) {
  let requests = 0;
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
  t.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(String(url), 'https://example.test/room/install.json');
    requests += 1;
    return response();
  });
  return {
    get requests() {
      return requests;
    },
    resume() {
      document.dispatchEvent(new Event('visibilitychange'));
      window.dispatchEvent(new Event('online'));
    },
  };
}

test('standalone runtime only checks after an explicit request', async (t) => {
  const env = environment(t);
  const runtime = browserRuntimeUpdates(undefined, 'installed', 100);
  env.resume();
  await setImmediate();
  assert.equal(env.requests, 0);
  await runtime.updates.check();
  assert.equal(env.requests, 1);
});

test('cached starter calls do not check for updates, while Settings can check', async (t) => {
  const env = environment(t);
  const starter = new BrowserUpdates('cached');
  const runtime = browserRuntimeUpdates(starter.host, 'installed', 100);
  // Older starters still invoke the bridged check on launch and browser events.
  const cachedEvent = () => {
    void starter.check();
  };
  document.addEventListener('visibilitychange', cachedEvent);
  window.addEventListener('online', cachedEvent);
  await starter.check();
  env.resume();
  await setImmediate();
  assert.equal(env.requests, 0);
  await runtime.updates.check();
  assert.equal(env.requests, 1);
  env.resume();
  await setImmediate();
  assert.equal(env.requests, 1);
});

test('a failed manual check can be retried explicitly', async (t) => {
  const env = environment(t, async () => {
    if (env.requests === 1) throw new Error('Network unavailable');
    return new Response(null, { status: 404 });
  });
  const updates = new BrowserUpdates('installed');
  let phase;
  updates.subscribe((state) => {
    phase = state.phase;
  });
  await updates.check();
  assert.equal(phase, 'error');
  env.resume();
  await setImmediate();
  assert.equal(env.requests, 1);
  await updates.check();
  assert.equal(env.requests, 2);
  assert.equal(phase, 'current');
});

test('concurrent explicit checks share the in-flight request', async (t) => {
  const deferred = Promise.withResolvers();
  const env = environment(t, () => deferred.promise);
  const updates = new BrowserUpdates('installed');
  const first = updates.check();
  const second = updates.check();
  assert.equal(second, first);
  await setImmediate();
  assert.equal(env.requests, 1);
  deferred.resolve(new Response(null, { status: 404 }));
  await Promise.all([first, second]);
});
