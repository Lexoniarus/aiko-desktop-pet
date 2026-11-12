import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { strToU8, zipSync } from 'fflate';
import {
  isLocalLaunch,
  selectLocalPackage,
} from '../src/platforms/browser/LocalLaunch.ts';
import { packageCachePrefix } from '../src/platforms/browser/PackageStore.ts';

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

const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');

function localPackages(t) {
  const installed = { id: 'first', version: 'first' };
  const settings = new Map([
    ['active', installed],
    ['pending', { id: 'staged' }],
  ]);
  const cacheName = (id) => packageCachePrefix + id;
  const names = new Set([
    'starter-shell',
    ...['first', 'staged', 'orphan'].map(cacheName),
  ]);
  const locks = new Set();
  const request = (result) => {
    const operation = { result };
    queueMicrotask(() => operation.onsuccess());
    return operation;
  };
  let failPruning = false;
  const replacements = {
    location: { href: 'http://127.0.0.1:8940/?local-launch=1' },
    indexedDB: {
      open: () =>
        request({
          transaction(_store, mode) {
            const tx = {
              objectStore: () => ({
                get: (key) => request(settings.get(key)),
                put: (value, key) => settings.set(key, value),
                delete: (key) => settings.delete(key),
              }),
            };
            if (mode === 'readwrite')
              queueMicrotask(() => queueMicrotask(() => tx.oncomplete()));
            return tx;
          },
          close() {},
        }),
    },
    caches: {
      keys() {
        assert.deepEqual([...locks], ['aiko-pet-writer', 'aiko-package-install']);
        if (failPruning) throw new Error('CacheStorage unavailable');
        return [...names];
      },
      delete: (name) => names.delete(name),
      open(name) {
        names.add(name);
        return { put() {} };
      },
    },
    navigator: {
      locks: {
        async request(name, ...args) {
          assert.ok(!locks.has(name), 'lock is non-reentrant');
          locks.add(name);
          try {
            return await args.at(-1)({});
          } finally {
            locks.delete(name);
          }
        },
      },
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
  const builds = new Map([[installed.version, 1]]);
  let offered, archive, onDownload;
  t.mock.method(globalThis, 'fetch', async (url) => {
    assert.ok(locks.has('aiko-pet-writer'));
    if (url.pathname === '/install.json') return Response.json(offered);
    if (url.pathname === '/' + offered.package) {
      onDownload?.();
      return new Response(archive);
    }
    assert.ok(url.pathname.endsWith('/runtime-assets.json'));
    const { version } = settings.get('active');
    return Response.json({
      packageVersion: version,
      buildTimestamp: builds.get(version),
    });
  });
  return {
    settings,
    names,
    cacheName,
    offer(version, { corrupt = false, downloaded } = {}) {
      const buildTimestamp = builds.size + 1;
      builds.set(version, buildTimestamp);
      const entry = strToU8('export function startRoom() {}');
      const manifest = strToU8(
        JSON.stringify({
          format: 1,
          protocol: 2,
          saveSchema: 7,
          version,
          entry: 'app.js',
          files: { 'app.js': { size: entry.length, sha256: hash(entry) } },
        }),
      );
      archive = zipSync({ 'manifest.json': manifest, 'app.js': entry });
      offered = {
        format: 1,
        version,
        buildTimestamp,
        package: 'packages/room.zip',
        size: archive.length,
        manifestSHA256: corrupt ? '0'.repeat(64) : hash(manifest),
      };
      onDownload = downloaded;
    },
    failPruningAfterDownload() {
      failPruning = true;
    },
  };
}

test('local upgrades prune unreferenced runtimes and failed ZIPs preserve the active package', async (t) => {
  const { settings, names, cacheName, offer } = localPackages(t);
  const select = () => selectLocalPackage(() => {});
  offer('second', {
    downloaded: () => {
      assert.ok(!names.has(cacheName('orphan')));
      assert.ok(names.has(cacheName('staged')));
    },
  });
  const second = await select();
  assert.equal(second.state, 'ready');
  assert.equal(settings.get('active').id, second.installed.id);
  assert.deepEqual(
    names,
    new Set(['starter-shell', cacheName('first'), cacheName(second.installed.id)]),
  );

  offer('third');
  const third = await select();
  assert.equal(third.state, 'ready');
  assert.equal(settings.get('previous').id, second.installed.id);
  const preserved = new Set([
    'starter-shell',
    cacheName(second.installed.id),
    cacheName(third.installed.id),
  ]);
  assert.deepEqual(names, preserved);

  offer('invalid', { corrupt: true });
  const rejected = await select();
  assert.equal(rejected.state, 'failed');
  assert.equal(rejected.offered, 'invalid');
  assert.equal(rejected.installed.id, third.installed.id);
  assert.equal(settings.get('active').id, third.installed.id);
  assert.deepEqual(names, preserved);
});

test('a cache maintenance failure after activation still opens the new package', async (t) => {
  const { settings, offer, failPruningAfterDownload } = localPackages(t);
  offer('second', { downloaded: failPruningAfterDownload });
  const result = await selectLocalPackage(() => {});
  assert.equal(result.state, 'ready');
  assert.equal(result.installed.version, 'second');
  assert.deepEqual(result.installed, settings.get('active'));
});
