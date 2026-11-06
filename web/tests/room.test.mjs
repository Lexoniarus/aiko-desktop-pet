import assert from 'node:assert/strict';
import test from 'node:test';
import { RoomProjection } from '../src/room/RoomProjection.ts';
import { readFileSync } from 'node:fs';
import {
  validPackagePath,
  validateManifest,
} from '../src/platforms/browser/PackageImporter.ts';
import { validatePublishedPackage } from '../src/platforms/browser/PublishedPackage.ts';
import { RoomMotion } from '../src/room/RoomMotion.ts';

const layout = JSON.parse(
  readFileSync(new URL('../../aiko_pet/assets/room/v1/layout.json', import.meta.url)),
);
test('floor projection round-trips after camera rotation and nearer Aiko is larger', () => {
  const projection = new RoomProjection(layout);
  for (const [yaw, point] of [
    [0, { x: 400, depth: 100 }],
    [Math.PI / 2, { x: 650, depth: 280 }],
    [Math.PI, { x: 430, depth: 500 }],
    [-Math.PI / 2, { x: 100, depth: 300 }],
  ]) {
    projection.update(1024, 768, yaw);
    const screen = projection.projectPoint(point),
      result = projection.intersectFloor(screen.x, screen.y);
    assert.ok(Math.abs(result.x - point.x) < 0.05);
    assert.ok(Math.abs(result.depth - point.depth) < 0.05);
  }
  projection.update(1024, 768, 0);
  assert.ok(
    projection.projectPoint({ x: 400, depth: 150 }).scale >
      projection.projectPoint({ x: 400, depth: 50 }).scale,
  );
});
test('display interpolation follows the admitted corner rather than its diagonal', () => {
  const motion = new RoomMotion();
  motion.receive({ x: 100, depth: 100 }, 1000);
  motion.receive({ x: 200, depth: 200 }, 1200, [
    { x: 100, depth: 100 },
    { x: 200, depth: 100 },
    { x: 200, depth: 200 },
  ]);
  assert.deepEqual(motion.position(1200), { x: 200, depth: 100 });
  motion.receive({ x: 200, depth: 200 }, 1300);
  assert.deepEqual(motion.position(1500), { x: 200, depth: 200 });
});
test('installer refuses traversal paths and incompatible package protocols', () => {
  for (const path of [
    '../state.sqlite3',
    '/outside.js',
    'app//file.js',
    'app/./file.js',
    'https://elsewhere/app.js',
  ])
    assert.equal(validPackagePath(path), false);
  assert.equal(validPackagePath('app/chunks/room-123.js'), true);
  assert.throws(() =>
    validateManifest({
      format: 1,
      protocol: 2,
      saveSchema: 6,
      version: 'x',
      entry: 'app.js',
      files: {},
    }),
  );
  const published = {
    format: 1,
    version: '0.1.0-test',
    package: 'packages/aiko.zip',
    size: 1024,
    manifestSHA256: 'a'.repeat(64),
  };
  assert.equal(validatePublishedPackage(published).version, published.version);
  for (const invalid of [
    { ...published, package: 'https://elsewhere/package.zip' },
    { ...published, package: 'packages/../outside.zip' },
    { ...published, size: Infinity },
    { ...published, manifestSHA256: 'missing' },
  ])
    assert.throws(() => validatePublishedPackage(invalid));
});
