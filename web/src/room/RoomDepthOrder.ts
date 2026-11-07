import type { RoomLayout, RoomPoint } from './RoomLayout';

/** Ground items cover the actor on the same cell, regardless of sub-cell motion. */
export function objectGroundOrder(
  layout: RoomLayout,
  pet: RoomPoint,
  object: RoomPoint,
  petGroundY: number,
  objectGroundY: number,
): number {
  const sameCell =
    Math.floor(pet.x / layout.cell_size) === Math.floor(object.x / layout.cell_size) &&
    Math.floor(pet.depth / layout.cell_size) ===
      Math.floor(object.depth / layout.cell_size);
  return Math.max(objectGroundY, sameCell ? petGroundY : -Infinity) + 0.01;
}
