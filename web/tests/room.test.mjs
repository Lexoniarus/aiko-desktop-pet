import assert from 'node:assert/strict';
import test from 'node:test';
import { RoomProjection } from '../src/room/RoomProjection.ts';
import { RoomCamera } from '../src/room/RoomCamera.ts';
import { readFileSync } from 'node:fs';
import {
  validPackagePath,
  validateManifest,
} from '../src/platforms/browser/PackageImporter.ts';
import {
  validatePublishedPackage,
  isNewerPublication,
} from '../src/platforms/browser/PublishedPackage.ts';
import { RoomMotion } from '../src/room/RoomMotion.ts';
import { roomWalkFrame } from '../src/room/RoomWalkPresentation.ts';
import { furnitureFrame } from '../src/room/RoomPresentation.ts';
import { objectGroundOrder } from '../src/room/RoomDepthOrder.ts';
import { canPlace, worldPoint, worldPolar } from '../src/room/RoomLayout.ts';
import {
  cellPoint,
  chipPoint,
  columnAt,
  landingCell,
  tableGameFrame,
  tableGamePan,
} from '../src/games/ConnectFourGeometry.ts';

test('table chips retain their diameter and flight joins the same landing geometry', () => {
  const frame = tableGameFrame({ x: 500, y: 700, width: 480, height: 150 });
  assert.equal(frame.chip, 26.24);
  assert.equal(frame.scale, 0.82);
  assert.equal(frame.y + 446 * frame.scale, 595);
  assert.ok(frame.playerY > 700);
  const half = tableGameFrame({ x: 250, y: 350, width: 240, height: 75 });
  assert.equal(half.chip, frame.chip / 2);
  assert.equal(columnAt(99.9), undefined);
  assert.equal(columnAt(100), 0);
  assert.equal(columnAt(379.9), 6);
  assert.equal(columnAt(380), undefined);
  const cells = Array(42).fill(0);
  assert.equal(landingCell(cells, 2), 37);
  for (let row = 0; row < 6; row++) cells[row * 7 + 2] = 1;
  assert.equal(landingCell(cells, 2), undefined);
  const start = { x: 560, y: 470 },
    seam = 1240 / 1490;
  const before = chipPoint(start, 35, seam - 1e-8, seam);
  const after = chipPoint(start, 35, seam, seam);
  assert.ok(Math.hypot(before.x - after.x, before.y - after.y) < 0.001);
  assert.deepEqual(chipPoint(start, 35, 1, seam), cellPoint(35));
});

const layout = JSON.parse(
  readFileSync(new URL('../../aiko_pet/assets/room/v1/layout.json', import.meta.url)),
);

test('feeding pan stays at room scale and a held drag pauses camera following', (t) => {
  const window = Object.assign(new EventTarget(), {
    matchMedia: () => ({ matches: false }),
  });
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'window');
  Object.defineProperty(globalThis, 'window', { configurable: true, value: window });
  t.after(() => {
    if (previous) Object.defineProperty(globalThis, 'window', previous);
    else delete globalThis.window;
  });
  let now = 0;
  t.mock.method(performance, 'now', () => now);
  const camera = new RoomCamera(new EventTarget(), layout);
  t.after(() => camera.destroy());
  camera.resize(393, 873);
  const point = { x: 700, depth: 300 };
  const scale = camera.projection.projectPoint(point).scale;
  const start = camera.yaw;
  const bearing = camera.projection.bearing(point);
  camera.panTo(point);
  now += 160;
  camera.tick(point);
  assert.ok(camera.yaw > start && camera.yaw < bearing);
  assert.equal(camera.sceneHeight, 873);
  assert.equal(camera.projection.projectPoint(point).scale, scale);
  now += 160;
  camera.tick(point);
  assert.equal(camera.panning, false);
  assert.equal(camera.projection.projectPoint(point).x, 393 / 2);
  camera.followPet();
  camera.hold(true);
  const other = { x: 380, depth: 140 };
  now += 100;
  camera.tick(other);
  assert.equal(camera.yaw, bearing);
  camera.hold(false);
  now += 100;
  camera.tick(other);
  assert.notEqual(camera.yaw, bearing);
});

test('wall furniture stays behind Aiko on free floor while its footprint stays blocked', () => {
  const projection = new RoomProjection(layout);
  projection.update(1024, 768, 0);
  const kitchen = layout.furniture.find((item) => item.id === 'kitchen');
  const beside = { x: 425, depth: 60 };
  assert.ok(canPlace(layout, beside, layout.pet_radius));
  assert.equal(canPlace(layout, { x: 350, depth: 20 }, layout.pet_radius), false);
  assert.equal(canPlace(layout, { x: 350, depth: 70 }, layout.pet_radius), false);
  assert.ok(
    furnitureFrame(projection, kitchen).order < projection.projectPoint(beside).groundY,
  );
  for (const item of layout.furniture.filter((item) => item.wall))
    assert.ok(furnitureFrame(projection, item).order < 0);
});

test('table and board share the floor order between front and rear walking positions', () => {
  const projection = new RoomProjection(layout);
  projection.update(1024, 768, Math.PI / 2);
  const table = furnitureFrame(
    projection,
    layout.furniture.find((item) => item.id === 'table'),
  );
  const board = tableGameFrame(table);
  assert.equal(board.order, table.order);
  for (const [point, inFront] of [
    [{ x: 600, depth: 300 }, true],
    [{ x: 730, depth: 300 }, false],
  ]) {
    assert.ok(canPlace(layout, point, layout.pet_radius));
    assert.equal(projection.projectPoint(point).groundY > board.order + 0.01, inFront);
  }
  const placement = layout.furniture.find((item) => item.id === 'table');
  projection.update(
    393,
    873,
    projection.bearing({ x: placement.x, depth: placement.z + placement.depth * 0.2 }),
  );
  const phone = tableGameFrame(furnitureFrame(projection, placement));
  const pan = tableGamePan(phone, 393);
  assert.ok(phone.x + 100 * phone.scale + pan >= 16 - 1e-8);
  assert.ok(phone.x + 380 * phone.scale + pan <= 393 - 16 + 1e-8);
  projection.update(
    768,
    1024,
    projection.bearing({ x: placement.x, depth: placement.z + placement.depth * 0.2 }),
  );
  assert.equal(
    tableGamePan(tableGameFrame(furnitureFrame(projection, placement)), 768),
    0,
  );
});

test('ground objects cover Aiko only when nearer or on the same depth', () => {
  const projection = new RoomProjection(layout);
  projection.update(1024, 768, 0);
  const ground = projection.projectPoint(worldPoint(layout, 0.4, 180)).groundY;
  for (const [distance, covered] of [
    [178, false],
    [180, true],
    [182, true],
  ]) {
    const pet = worldPoint(layout, 0.4, distance);
    const petY = projection.projectPoint(pet).groundY;
    assert.equal(objectGroundOrder(ground) > petY, covered);
  }
});

test('food drag has one floor line and scale while vertical movement changes height', () => {
  const projection = new RoomProjection(layout);
  let scale;
  for (const yaw of [0, Math.PI / 2, Math.PI, -Math.PI / 2, Math.PI / 4]) {
    projection.update(1024, 768, yaw);
    const low = projection.foodPlacement(512, 700),
      high = projection.foodPlacement(512, 400);
    assert.deepEqual(low.point, high.point);
    assert.ok(high.height > low.height);
    const screen = projection.projectPoint(low.point);
    scale ??= screen.scale;
    assert.ok(Math.abs(screen.scale - scale) < 1e-8);
    assert.ok(Math.abs(screen.depth - 175.43859649122805) < 1e-8);
    assert.ok(
      Math.abs(screen.groundY - (802 + 88 * layout.food_line) * projection.fit) < 1e-8,
    );
  }
});
test('flat panorama preserves floor and lifted drop coordinates in every direction', () => {
  const projection = new RoomProjection(layout);
  for (const [yaw, point] of [
    [0, { x: 400, depth: 100 }],
    [Math.PI / 2, { x: 650, depth: 280 }],
    [Math.PI, { x: 430, depth: 500 }],
    [-Math.PI / 2, { x: 100, depth: 300 }],
    [Math.PI / 4, { x: 700, depth: 74.99 }],
    [Math.PI / 4, { x: 700, depth: 75.01 }],
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

test('four wall grids have one window and use the authored furniture proportions', () => {
  assert.equal(new Set(layout.walls.map((wall) => wall.id)).size, 4);
  assert.deepEqual(
    layout.walls.filter((wall) => wall.asset === 'living').map((wall) => wall.id),
    ['east'],
  );
  const projection = new RoomProjection(layout);
  projection.update(1800, 900, 0);
  const item = (id) => layout.furniture.find((item) => item.id === id);
  const door = furnitureFrame(projection, item('door'));
  assert.ok(Math.abs(door.x - 270) < 1e-6);
  assert.equal(door.y, 802);
  assert.equal(door.width, 255);
  assert.equal(furnitureFrame(projection, item('bed')).width, 680);
  assert.equal(furnitureFrame(projection, item('table')).width, 527);
  projection.update(1800, 900, -Math.PI / 2);
  const shelf = furnitureFrame(projection, item('shelf'));
  assert.ok(Math.abs(shelf.x - 660) < 1e-6);
  assert.equal(shelf.y, 540);
  assert.equal(shelf.width, 270);
  const plant = furnitureFrame(projection, item('plant'));
  assert.ok(plant.x - plant.width / 2 >= 18);
  projection.update(1800, 900, Math.PI);
  const bed = furnitureFrame(projection, item('bed'));
  assert.ok(bed.x - bed.width / 2 >= 18);
  assert.equal(bed.flipX, true);
  for (const entry of layout.furniture) {
    const frame = furnitureFrame(projection, entry);
    assert.ok(
      Math.abs(frame.width / frame.height - entry.crop[2] / entry.crop[3]) < 1e-6,
    );
  }
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
test('Aiko crosses the seam behind an apple, approaches on one ray and returns in front', () => {
  const projection = new RoomProjection(layout);
  const motion = new RoomMotion(layout);
  projection.update(1024, 900, Math.PI / 4);
  const apple = projection.projectPoint(projection.foodPlacement(512, 859.2).point);
  const seam = Math.atan2(layout.width, layout.depth);
  const left = seam - 0.095,
    right = seam + 0.095;
  const far = 225,
    near = 145;
  const stepLength = (16 * 100) / 156;
  const speed = stepLength / 0.62;
  const route = [
    { angle: left, distance: far, distanceWalked: 0 },
    { angle: right, distance: far, distanceWalked: 0.19 * far },
    { angle: right, distance: near, distanceWalked: 0.19 * far + far - near },
    { angle: left, distance: near, distanceWalked: 0.19 * (far + near) + far - near },
  ];
  const points = route.map(({ angle, distance }) =>
    worldPoint(layout, angle, distance),
  );
  const length = route.at(-1).distanceWalked;
  motion.receive(points[0], 1000, [], {
    time: 0,
    distance: 0,
    step_length: stepLength,
  });
  motion.receive(points.at(-1), 1000 + (1000 * length) / speed, points, {
    time: length / speed,
    distance: length,
    step_length: stepLength,
  });
  const sample = (distance) => {
    const { point, walk } = motion.sample(1100 + (1000 * distance) / speed);
    return { ...projection.projectPoint(point), walk };
  };
  const nearEqual = (a, b) => assert.ok(Math.abs(a - b) < 1e-7);
  const back = [0.25, 0.5, 0.75].map((t) => sample(route[1].distanceWalked * t));
  const front = [0.25, 0.5, 0.75].map((t) =>
    sample(route[2].distanceWalked + 0.19 * near * t),
  );
  for (const [row, clip, appleInFront] of [
    [back, 'body-step-right-profil', true],
    [front, 'body-step-left-profil', false],
  ]) {
    for (const frame of row) {
      nearEqual(frame.scale, row[0].scale);
      nearEqual(frame.groundY, row[0].groundY);
      assert.equal(frame.walk.clip, clip);
      assert.equal(objectGroundOrder(apple.groundY) > frame.groundY, appleInFront);
    }
    nearEqual(row[1].x, apple.x);
    assert.equal(row[0].x < row[2].x, appleInFront);
  }
  assert.ok(front[1].scale > back[1].scale);
  const projectedStride = projection.profileStepLength(stepLength);
  for (const radius of [far, near]) {
    const a = projection.projectPoint(worldPoint(layout, seam, radius));
    const b = projection.projectPoint(
      worldPoint(layout, seam + projectedStride / radius, radius),
    );
    const strideInPixels = a.scale * stepLength;
    assert.ok(Math.abs(b.x - a.x - strideInPixels) < 0.06 * strideInPixels);
  }
  const one = sample(route[1].distanceWalked + 10);
  const two = sample(route[1].distanceWalked + 20);
  const three = sample(route[1].distanceWalked + 30);
  for (const frame of [one, two, three]) {
    nearEqual(frame.x, one.x);
    assert.equal(frame.walk.clip, 'room-walk-toward');
  }
  nearEqual(two.walk.distance - one.walk.distance, 10);
  nearEqual(three.walk.distance - two.walk.distance, 10);
  assert.ok(one.groundY < two.groundY && two.groundY < three.groundY);
  assert.ok(one.scale < two.scale && two.scale < three.scale);
  nearEqual(
    (two.groundY - one.groundY) / (two.scale - one.scale),
    (three.groundY - two.groundY) / (three.scale - two.scale),
  );
  assert.ok(
    front[2].walk.distance - front[0].walk.distance <
      back[2].walk.distance - back[0].walk.distance,
  );
});

test('gait frames follow stride distance and the actor stops within the last tick', () => {
  const stepLength = (16 * 100) / 156;
  const clip = { duration: 1.24, order: [], frames: Array(8).fill({ duration: 155 }) };
  assert.equal(roomWalkFrame(clip, 0, stepLength), 0);
  assert.equal(roomWalkFrame(clip, stepLength * 0.3, stepLength), 1);
  assert.equal(roomWalkFrame(clip, stepLength, stepLength), 4);
  assert.equal(roomWalkFrame(clip, stepLength * 2, stepLength), 0);

  const motion = new RoomMotion(layout);
  const start = worldPoint(layout, -0.37, 224);
  const end = worldPoint(layout, -0.37, 220);
  motion.receive(start, 1000, [], { time: 0, distance: 0, step_length: stepLength });
  motion.receive(end, 1500, [start, end], {
    time: 0.5,
    distance: 4,
    step_length: stepLength,
  });
  const mid = motion.sample(1220);
  assert.equal(mid.walk.clip, 'room-walk-toward');
  assert.ok(Math.abs(worldPolar(layout, mid.point).distance - 222) < 0.02);
  assert.deepEqual(motion.sample(1350), { point: end, walk: undefined });
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
    { ...published, buildTimestamp: -1 },
    { ...published, buildTimestamp: 'tomorrow' },
  ])
    assert.throws(() => validatePublishedPackage(invalid));
});

test('a manual runtime accepts newer publications without reverting to a stale feed', () => {
  assert.equal(isNewerPublication('local', 200, { version: 'legacy' }), false);
  assert.equal(
    isNewerPublication('local', 200, { version: 'old', buildTimestamp: 100 }),
    false,
  );
  assert.equal(
    isNewerPublication('local', 200, { version: 'other', buildTimestamp: 200 }),
    false,
  );
  assert.equal(
    isNewerPublication('local', 200, { version: 'local', buildTimestamp: 300 }),
    false,
  );
  assert.equal(
    isNewerPublication('local', 200, { version: 'next', buildTimestamp: 300 }),
    true,
  );
  assert.equal(isNewerPublication('legacy', 0, { version: 'initial-update' }), true);
});
