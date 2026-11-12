import type { PlayerApproach } from '../bridge/RoomClient';
import type { RoomPoint } from './RoomLayout';

export function approachScale(depth: number): number {
  return 0.23 + 0.425 * (0.64 * depth + 0.36 * depth * depth);
}

/** Fit the approved portrait compositions to the rendered room height. */
export function playerFraming(
  approach: PlayerApproach | null | undefined,
  point: RoomPoint,
  sceneHeight: number,
  petHeight: number,
  base: { y: number; scale: number },
): { y: number; scale: number } {
  if (!approach?.active) return base;
  const { entry, target, framing } = approach;
  const depthAxis = entry.x === target.x;
  if (
    depthAxis
      ? Math.abs(point.x - entry.x) > 1e-6
      : Math.abs(point.depth - entry.depth) > 1e-6
  )
    return base;

  const fraction = depthAxis
    ? (point.depth - entry.depth) / (target.depth - entry.depth)
    : (point.x - entry.x) / (target.x - entry.x);
  if (fraction <= 0) return base;
  const progress = Math.min(1, fraction) * framing;
  const blend = Math.min(1, progress / 0.5);
  const ease = blend * blend * (3 - 2 * blend);
  const size = (sceneHeight * (1158 / 800) * approachScale(progress)) / petHeight;
  const foot =
    (sceneHeight / 800) *
    (772 + 278 * (0.55 * progress + 0.45 * progress ** 2) - 40 * progress ** 2);
  return {
    y: base.y + Math.max(0, foot - base.y) * ease,
    scale: base.scale + Math.max(0, size - base.scale) * ease,
  };
}
