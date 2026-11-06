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
test('flat panorama preserves floor and lifted drop coordinates in every direction', () => {
  const projection = new RoomProjection(layout);
  for (const [yaw, point] of [
    [0, { x: 400, depth: 100 }],
    [Math.PI / 2, { x: 650, depth: 280 }],
    [Math.PI, { x: 430, depth: 500 }],
    [-Math.PI / 2, { x: 100, depth: 300 }],
  ]) {
    projection.update(1024, 768, yaw);
    for (const height of [0, 25]) {
      const screen = projection.projectPoint(point, height),
        result = projection.intersectFloor(screen.x, screen.y, height);
      assert.ok(Math.abs(result.x - point.x) < 0.05);
      assert.ok(Math.abs(result.depth - point.depth) < 0.05);
    }
  }
  projection.update(1024, 768, 0);
  assert.ok(
    projection.projectPoint({ x: 400, depth: 150 }).scale >
      projection.projectPoint({ x: 400, depth: 50 }).scale,
  );
});
test('panning only translates art, including across the panorama wrap', () => {
  const projection = new RoomProjection(layout);
  const point = { x: 430, depth: 500 };
  projection.update(1024, 768, Math.PI - 0.1);
  const before = projection.projectPoint(point, 40);
  projection.update(1024, 768, -Math.PI + 0.1);
  const after = projection.projectPoint(point, 40);
  assert.equal(after.scale, before.scale);
  assert.equal(after.y, before.y);
  assert.ok(Math.abs(after.x - before.x + 0.2 * projection.angularScale) < 1e-6);
  const held = projection.atDistance(after.x, after.y, point);
  assert.ok(Math.hypot(held.point.x - point.x, held.point.depth - point.depth) < 1e-6);
  assert.ok(Math.abs(held.height - 40) < 1e-6);
  assert.equal(projection.intersectFloor(512, 10), undefined);
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
