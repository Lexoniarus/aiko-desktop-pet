/** v16 room projection. Depth stays separate from height above the floor. */
export const roomWidth = 5100;
export const wrap = (x: number): number => ((x % roomWidth) + roomWidth) % roomWidth;
export const delta = (from: number, to: number): number =>
  ((to - from + roomWidth * 1.5) % roomWidth) - roomWidth / 2;
export const depthScale = (depth: number): number => {
  const d = Math.min(1.55, Math.max(0.2, depth));
  return 0.88 + d * 0.16 + ((0.55 - 0.16) / 0.55) * Math.max(0, d - 1) ** 2;
};
export const feetY = (depth: number): number =>
  802 +
  76 * Math.min(depth, 1) +
  (76 / 0.16) * Math.max(0, depthScale(depth) - depthScale(1));
export const projectX = (x: number, depth: number, center: number): number =>
  center + (delta(center, x) * depthScale(depth)) / depthScale(0.9);
export function unproject(
  x: number,
  y: number,
  center: number,
): { x: number; depth: number } {
  let low = 0.2,
    high = 1.55;
  for (let i = 0; i < 24; i++) {
    const middle = (low + high) / 2;
    if (feetY(middle) < y) low = middle;
    else high = middle;
  }
  const depth = (low + high) / 2;
  return {
    x: wrap(center + ((x - center) * depthScale(0.9)) / depthScale(depth)),
    depth,
  };
}
