import type { FurniturePlacement, RoomLayout, RoomPoint } from './RoomLayout';
import type { RoomProjection } from './RoomProjection';

/** Camera calibration for the flat panorama at the reference scene height. */
export const roomPresentation = {
  designHeight: 900,
  panelWidth: 1800,
  focalLength: 990,
  horizon: 0.3,
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
  const layout = projection.layout;
  const support = furnitureSupport(layout, item);
  const ground = projection.projectPoint(support);
  const scale = (item.height * ground.scale) / item.crop[3];
  const surface = projection.projectPoint(support, item.height);
  const y =
    item.id === 'door'
      ? projection.floorLine
      : ground.y - (item.elevation ?? 0) * ground.scale;
  return {
    x: ground.x,
    y,
    scale,
    width: item.crop[2] * scale,
    height: item.crop[3] * scale,
    surface,
    order: item.wall ? -1000 + ground.groundY / 10000 : ground.groundY,
    flipX: item.id === 'bed',
  };
}
