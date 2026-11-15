/** Measurements from the accepted north-wall and close-call previews. */
export const northWallArtwork = {
  wallHeight: 350,
  sceneHeight: 544,
  pixelsPerUnit: 2.2,
  aikoHeight: 121.275,
  doorHeight: 120.1725,
  fridgeHeight: 120.1725,
  kitchenHeight: 67,
  kitchenFloorOffset: 38,
  fridgeFloorOffset: 36,
  cupboardBottom: 194,
  cupboardWidth: 0.88,
} as const;

const reference = northWallArtwork;
const rearFootOffset = 51;
const rearRow = 95;
const parallelRowsEnd = 115;
const frontFraction = (520 - 401) / (670.42554925 - 401);
const closeHeightFraction = 486.2521125 / reference.sceneHeight;
const closeCrop = 0.26;

export function northWallBlend(bearing: number): number {
  const blend = Math.max(0, Math.min(1, (1.24 - Math.abs(bearing)) / 0.28));
  return blend * blend * (3 - 2 * blend);
}

/** Cubic interpolation with the same derivative on both sides of each join. */
export function floorCurve(
  start: number,
  end: number,
  span: number,
  distance: number,
  startSlope: number,
  endSlope: number,
): number {
  const t = distance / span;
  const a = startSlope * span;
  const b = endSlope * span;
  const delta = end - start;
  return start + t * (a + t * (3 * delta - 2 * a - b + t * (a + b - 2 * delta)));
}

export function northDepth({
  radius,
  bearing,
  wallAxis,
  frontRadius,
  closeRadius,
  wallLine,
  viewportHeight,
  petHeight,
  maxScale = Infinity,
}: {
  radius: number;
  bearing: number;
  wallAxis: number;
  frontRadius: number;
  closeRadius: number;
  wallLine: number;
  viewportHeight: number;
  petHeight: number;
  maxScale?: number;
}) {
  const wallScale = wallLine / reference.wallHeight;
  const rearY = wallLine + rearFootOffset * wallScale;
  const rearScale = Math.min(
    (reference.aikoHeight * reference.pixelsPerUnit * wallScale) / petHeight,
    maxScale,
  );
  const closeScale = Math.min(
    (viewportHeight * closeHeightFraction) / petHeight,
    maxScale,
  );
  const closeY = viewportHeight + closeCrop * petHeight * closeScale;
  const frontY = rearY + (closeY - rearY) * frontFraction;
  const cosine = Math.cos(bearing);
  const joinRadius = (wallAxis - parallelRowsEnd) / cosine;
  const joinY = wallLine + (rearFootOffset * wallScale * parallelRowsEnd) / rearRow;
  const rearSlope = (rearFootOffset * wallScale * cosine) / rearRow;
  const normalSpan = joinRadius - frontRadius;
  const closeSpan = frontRadius - closeRadius;
  const normalSlope = (frontY - joinY) / normalSpan;
  const closeSlope = (closeY - frontY) / closeSpan;
  const frontSlope = Math.min(normalSlope * 1.45, closeSlope);

  let groundY: number;
  if (radius >= joinRadius) {
    // Along a row parallel to the north wall, lateral position has no effect.
    groundY =
      wallLine + ((wallAxis - radius * cosine) * rearFootOffset * wallScale) / rearRow;
  } else if (radius >= frontRadius) {
    groundY = floorCurve(
      joinY,
      frontY,
      normalSpan,
      joinRadius - radius,
      rearSlope,
      frontSlope,
    );
  } else {
    groundY = floorCurve(
      frontY,
      closeY,
      closeSpan,
      frontRadius - Math.max(closeRadius, radius),
      frontSlope,
      closeSlope * 1.35,
    );
  }
  const progress = (groundY - rearY) / (closeY - rearY);
  return { groundY, scale: rearScale + (closeScale - rearScale) * progress };
}
