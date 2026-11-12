import assert from 'node:assert/strict';
import test from 'node:test';
import {
  isLocalLaunch,
  selectLocalPackage,
} from '../src/platforms/browser/LocalLaunch.ts';

test('the launch marker is recognized only on the local starter entry', () => {
  assert.equal(isLocalLaunch(new URL('http://127.0.0.1:8940/?local-launch=1')), true);
  for (const address of [
    'http://127.0.0.1:8940/',
    'http://127.0.0.1:8940/?local-launch=0',
    'http://127.0.0.1:8940/room/?local-launch=1',
    'http://localhost:8940/?local-launch=1',
    'http://127.0.0.1:8941/?local-launch=1',
    'https://example.test/room/?local-launch=1',
  ]) {
    assert.equal(isLocalLaunch(new URL(address)), false, address);
  }
});

test('local package selection stops before network access while Aiko holds the writer lock', async (t) => {
  const navigator = Object.getOwnPropertyDescriptor(globalThis, 'navigator');
  Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    value: {
      locks: {
        request(name, options, callback) {
          assert.equal(name, 'aiko-pet-writer');
          assert.deepEqual(options, { ifAvailable: true });
          return callback(null);
        },
      },
    },
  });
  t.after(() => Object.defineProperty(globalThis, 'navigator', navigator));
  const fetch = t.mock.method(globalThis, 'fetch');
  assert.deepEqual(await selectLocalPackage(() => {}), { state: 'busy' });
  assert.equal(fetch.mock.callCount(), 0);
});
