/** Shared palm contact for every item; no per-item grip offsets in V3. */
export function heldItemPosition(
  palm: [number, number],
  origin: [number, number],
  height: number,
): [number, number] {
  return [
    (palm[0] - origin[0]) * 2,
    Math.min(palm[1] * 2, 388 - height / 2) - origin[1] * 2,
  ];
}
