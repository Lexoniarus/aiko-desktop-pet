import type { FurniturePlacement, RoomLayout, RoomPoint } from './RoomLayout';
import type { RoomProjection } from './RoomProjection';

/** Authored v16 picture dimensions, independent of collision-box dimensions. */
export const roomPresentation = {
  designHeight: 900,
  panelWidth: 1800,
  floorBack: 802,
  floorFront: 890,
  furniture: {
    door: { width: 255 },
    kitchen: { width: (475 * 964) / 1183 },
    fridge: { width: 244 },
    table: { width: 527 },
    bed: { width: 680, flipX: true },
    desk: { width: 386 },
    shelf: { width: 270, mount: 262 },
    plant: { width: 204 },
  } as Record<string, { width: number; mount?: number; flipX?: boolean }>,
} as const;

export function furnitureSupport(
  layout: RoomLayout,
  item: FurniturePlacement,
): RoomPoint {
  const point = { x: item.x, depth: item.z };
  if (!item.blocking) return point;
  if (item.wall === 'north') point.depth += item.depth / 2;
  else if (item.wall === 'south') point.depth -= item.depth / 2;
  else if (item.wall === 'east') point.x -= item.width / 2;
  else if (item.wall === 'west') point.x += item.width / 2;
  else if (Math.abs(layout.width / 2 - item.x) > Math.abs(layout.depth / 2 - item.z))
    point.x += (Math.sign(layout.width / 2 - item.x) * item.width) / 2;
  else point.depth += (Math.sign(layout.depth / 2 - item.z) * item.depth) / 2;
  return point;
}

export function furnitureFrame(projection: RoomProjection, item: FurniturePlacement) {
  const ground = projection.projectPoint(furnitureSupport(projection.layout, item));
  const profile = roomPresentation.furniture[item.id]!;
  const scale = (profile.width * projection.fit) / item.crop[2];
  const width = item.crop[2] * scale;
  let x = ground.x;
  if (item.wall) {
    const angles: Record<string, number> = {
      north: 0,
      east: Math.PI / 2,
      south: Math.PI,
      west: -Math.PI / 2,
    };
    const centre = projection.screenX(angles[item.wall]!);
    const halfWall = (projection.panelWidth * projection.fit) / 2;
    const margin = 18 * projection.fit;
    const pivot = profile.flipX ? 1 - item.pivot[0] : item.pivot[0];
    // Art can overhang its support point, but never cross a room-wall joint.
    x = Math.max(
      centre - halfWall + width * pivot + margin,
      Math.min(centre + halfWall - width * (1 - pivot) - margin, x),
    );
  }
  return {
    x,
    y: ground.groundY - (profile.mount ?? 0) * projection.fit,
    scale,
    width,
    height: item.crop[3] * scale,
    // Wall art can overhang its physical footprint. It must never cover an
    // actor on free floor beside it; freestanding furniture retains depth.
    order: item.wall ? -1000 + ground.groundY / 10000 : ground.groundY,
    flipX: profile.flipX ?? false,
  };
}
