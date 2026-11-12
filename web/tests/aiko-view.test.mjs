import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Assets, Texture } from 'pixi.js';
import { AikoView } from '../src/room/AikoView.ts';

const root = 'https://room.test/';
const settle = () => new Promise((resolve) => setImmediate(resolve));

function clip(name, anchor, order = []) {
  return {
    frames: [0, 1].map((index) => ({
      file: `${name}-${index}.png`,
      duration: 100 + index * 40,
      bounds: [10 + index, 20, 60 + index, 100],
      foodAnchor: [40 + index, 50],
      foreground: null,
    })),
    order,
    loop: false,
    anchor,
    duration: 0.24,
  };
}

function createView(t) {
  const clips = {
    idle: clip('idle', [20, 40]),
    'body-turn-left': clip('turn', [25, 44], [1, 0]),
    'expression-positive': clip('positive', [30, 50]),
    'expression-worried': clip('worried', [29, 48]),
  };
  const textures = new Map();
  const waits = new Map();
  const errors = [];
  const load = t.mock.method(Assets, 'load', (url) => {
    const file = new URL(url).pathname.slice(1);
    if (!textures.has(file))
      textures.set(file, new Texture({ source: Texture.WHITE.source }));
    return waits.get(file)?.promise ?? Promise.resolve(textures.get(file));
  });
  const view = new AikoView(
    root,
    clips,
    { apple: { file: 'apple.png', pivot: [0, 0] } },
    (error) => errors.push(error),
  );
  t.after(() => view.destroy());
  return { view, textures, waits, errors, load };
}

function assertPose(view, textures, file, clipName, index, anchor) {
  assert.equal(view.sprite.texture, textures.get(file));
  assert.equal(view.clipName, clipName);
  assert.equal(view.sprite.currentFrame, index);
  assert.deepEqual(
    [view.sprite.anchor.x, view.sprite.anchor.y],
    [anchor[0] / 192, anchor[1] / 208],
  );
  const bounds = view.screenBounds();
  assert.deepEqual(
    [bounds.originX, bounds.originY],
    anchor.map((value) => -value * 2),
  );
  const source = Number(file.at(-5));
  assert.deepEqual(
    [bounds.x, bounds.y],
    [10 + source - 2 * anchor[0], 20 - 2 * anchor[1]],
  );
  assert.equal(view.held.visible, true);
  assert.deepEqual(
    [view.held.x, view.held.y],
    [2 * (40 + source - anchor[0]), 2 * (50 - anchor[1])],
  );
}

test('a prepared first turn draws the requested frame and its anchors synchronously', async (t) => {
  const { view, textures, load } = createView(t);
  await view.prepareRoom();
  view.show('idle', 0, null, 0);
  await view.hold('apple');
  const before = load.mock.callCount();

  view.showFromCamera('body-turn-left', -1, 0, undefined, false, 1, null, 0);

  assert.equal(load.mock.callCount(), before);
  assertPose(view, textures, 'turn-0.png', 'body-turn-left', 1, [25, 44]);
});

test('pending requests keep the visible pose and draw only the latest confirmed frame', async (t) => {
  const { view, textures, waits, load } = createView(t);
  const positive = Promise.withResolvers();
  const worried = Promise.withResolvers();
  waits.set('positive-0.png', positive);
  waits.set('worried-0.png', worried);
  await view.prepareRoom();
  view.show('idle', 0, null, 0);
  await view.hold('apple');
  const before = load.mock.callCount();

  view.show('expression-positive', 1, null, 0);
  view.show('expression-positive', 1, null, 1);
  assert.equal(load.mock.callCount() - before, 2);
  assertPose(view, textures, 'idle-0.png', 'idle', 0, [20, 40]);

  view.show('expression-worried', 2, null, 0);
  view.show('expression-worried', 2, null, 1);
  worried.resolve(textures.get('worried-0.png'));
  await settle();
  assertPose(view, textures, 'idle-0.png', 'idle', 0, [20, 40]);
  view.show('expression-worried', 2, null, 1);
  assertPose(view, textures, 'worried-1.png', 'expression-worried', 1, [29, 48]);

  positive.resolve(textures.get('positive-0.png'));
  await settle();
  assertPose(view, textures, 'worried-1.png', 'expression-worried', 1, [29, 48]);
});

test('a failed clip reports once and leaves the visible texture and anchors intact', async (t) => {
  const { view, textures, waits, errors, load } = createView(t);
  const failure = Promise.withResolvers();
  waits.set('positive-0.png', failure);
  await view.prepareRoom();
  view.show('idle', 0, null, 0);
  await view.hold('apple');

  view.show('expression-positive', 1, null, 0);
  failure.reject(new Error('missing texture'));
  await settle();
  const before = load.mock.callCount();
  view.show('expression-positive', 1, null, 1);
  assert.equal(load.mock.callCount(), before);
  assert.equal(errors.length, 1);
  assert.match(errors[0].message, /expression-positive/);
  assertPose(view, textures, 'idle-0.png', 'idle', 0, [20, 40]);

  view.show('body-turn-left', 2, null, 1);
  assertPose(view, textures, 'turn-1.png', 'body-turn-left', 0, [25, 44]);
});
