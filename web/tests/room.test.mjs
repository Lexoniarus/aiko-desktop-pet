import assert from 'node:assert/strict';
import test from 'node:test';
import {
  depthScale,
  feetY,
  projectX,
  unproject,
  wrap,
} from '../src/room/RoomProjection.ts';
import {
  validPackagePath,
  validateManifest,
} from '../src/platforms/browser/PackageImporter.ts';
import { validatePublishedPackage } from '../src/platforms/browser/PublishedPackage.ts';

test('room projection round-trips depth at the wrap boundary', () => {
  for (const [x, depth, center] of [
    [10, 0.2, 5000],
    [4800, 0.9, 50],
    [2100, 1.55, 2450],
  ]) {
    const result = unproject(projectX(x, depth, center), feetY(depth), center);
    assert.ok(Math.abs(result.x - x) < 0.01);
    assert.ok(Math.abs(result.depth - depth) < 0.001);
  }
  assert.equal(wrap(-10), 5090);
  assert.ok(depthScale(1.55) > depthScale(0.9));
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
