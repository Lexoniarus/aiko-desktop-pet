import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { heldItemPosition } from '../src/room/heldItemPosition.ts';

test('food and books share one palm point without individual grip offsets', () => {
  assert.deepEqual(heldItemPosition([96, 147], [96, 194], 50), [0, -94]);
  assert.deepEqual(heldItemPosition([96, 147], [96, 194], 100), [0, -94]);
  assert.deepEqual(heldItemPosition([73.5, 137], [96, 194], 50), [-45, -114]);
});

test('large held items stay above the same ground plane while grasping', () => {
  assert.deepEqual(heldItemPosition([96, 186], [96, 194], 50), [0, -25]);
  assert.deepEqual(heldItemPosition([96, 186], [96, 194], 100), [0, -50]);
});

test('authored throw releases from its actual palm instead of legacy frame five', () => {
  const family = JSON.parse(
    readFileSync(new URL('../../aiko_pet/assets/actions/grasp.json', import.meta.url)),
  );
  const frames = family.clips.throw_item.frames;
  const release = frames.findIndex((f) => f.events.includes('release_object'));
  const attach = frames.findIndex((f) => f.events.includes('attach_object'));
  assert.ok(attach > 3 && release > attach);
  assert.notEqual(release, 5);
  assert.deepEqual(frames[release - 1].food_anchor, [96, 136]);
  assert.ok(frames.slice(release).every((f) => f.food_anchor === null));
});
