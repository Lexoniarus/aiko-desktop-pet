/** Exported from the same layout used by the Python room owners. */
export interface RoomPoint {
  x: number;
  depth: number;
}

export function worldPolar(layout: RoomLayout, point: RoomPoint) {
  const x = point.x - layout.width / 2;
  const z = layout.depth / 2 - point.depth;
  return { bearing: Math.atan2(x, z), distance: Math.hypot(x, z) };
}

export function worldPoint(
  layout: RoomLayout,
  bearing: number,
  distance: number,
): RoomPoint {
  return {
    x: layout.width / 2 + distance * Math.sin(bearing),
    depth: layout.depth / 2 - distance * Math.cos(bearing),
  };
}
export interface FurniturePlacement {
  id: string;
  asset: string;
  x: number;
  z: number;
  width: number;
  depth: number;
  height: number;
  wall: string | null;
  elevation: number;
  blocking: boolean;
  crop: [number, number, number, number];
  pivot: [number, number];
}
export interface RoomLayout {
  walls: Array<{ id: string; asset: string }>;
  id: string;
  revision: number;
  width: number;
  depth: number;
  wall_height: number;
  cell_size: number;
  pet_height: number;
  pet_radius: number;
  camera_height: number;
  camera_clearance: number;
  food_line: number;
  furniture: FurniturePlacement[];
}
export function canPlace(layout: RoomLayout, point: RoomPoint, radius = 6): boolean {
  return (
    point.x >= radius &&
    point.x <= layout.width - radius &&
    point.depth >= radius &&
    point.depth <= layout.depth - radius &&
    Math.hypot(point.x - layout.width / 2, point.depth - layout.depth / 2) >=
      layout.camera_clearance + radius &&
    !layout.furniture.some(
      (item) =>
        item.blocking &&
        Math.abs(point.x - item.x) <= item.width / 2 + radius &&
        Math.abs(point.depth - item.z) <= item.depth / 2 + radius,
    )
  );
}
