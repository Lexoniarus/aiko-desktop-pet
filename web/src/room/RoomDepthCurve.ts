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

/** Source and projected seam heights, measured in the accepted floor preview. */
export const floorArtwork = {
  sourceRows: [0, 26, 60, 101, 147, 201, 262, 333, 417, 511, 616, 724],
  displayRows: [0, 16, 34, 54, 74, 96, 120, 145, 173, 203, 235, 268],
} as const;

const kitchenDepth = 100;
const kitchenFloorRow = 2.4336182874105674;
const frontFloorRow = 8.804220715278788;
const walkRowSpan = frontFloorRow - kitchenFloorRow;
const rows = floorArtwork.displayRows;
const rowHeights = rows.slice(1).map((end, index) => end - rows[index]!);
const rowSlopes = rows.map((_, index) => {
  const previous = rowHeights[Math.max(0, index - 1)]!;
  const next = rowHeights[Math.min(index, rowHeights.length - 1)]!;
  // Match the tangents of neighboring rows without overshooting a seam.
  return (2 * previous * next) / (previous + next);
});

function paintedFloorY(row: number): number {
  const index = Math.floor(row);
  return floorCurve(
    rows[index]!,
    rows[index + 1]!,
    1,
    row - index,
    rowSlopes[index]!,
    rowSlopes[index + 1]!,
  );
}

const kitchenPaintedY = paintedFloorY(kitchenFloorRow);
const paintedWalkSpan = paintedFloorY(frontFloorRow) - kitchenPaintedY;

function paintedWalkSlope(row: number): number {
  const index = Math.floor(row);
  const t = row - index;
  const start = rowSlopes[index]!;
  const end = rowSlopes[index + 1]!;
  const height = rowHeights[index]!;
  const slope =
    start +
    t * (2 * (3 * height - 2 * start - end) + t * 3 * (start + end - 2 * height));
  return (slope * walkRowSpan) / paintedWalkSpan;
}

const kitchenWalkSlope = paintedWalkSlope(kitchenFloorRow);
const frontWalkSlope = paintedWalkSlope(frontFloorRow);

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
  paintedFloor = false,
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
  paintedFloor?: boolean;
}) {
  const wallScale = wallLine / reference.wallHeight;
  const rearY = wallLine + rearFootOffset * wallScale;
  const rearScale = Math.min(
    (reference.aikoHeight * reference.pixelsPerUnit * wallScale) / petHeight,
    maxScale,
  );
  const fullCloseScale = (viewportHeight * closeHeightFraction) / petHeight;
  const closeScale = Math.min(fullCloseScale, maxScale);
  const closeY = viewportHeight + closeCrop * petHeight * closeScale;
  const floorCloseY = paintedFloor
    ? viewportHeight + closeCrop * petHeight * fullCloseScale
    : closeY;
  const frontY = rearY + (floorCloseY - rearY) * frontFraction;
  const cosine = Math.cos(bearing);
  const joinDepth = paintedFloor ? kitchenDepth : parallelRowsEnd;
  const joinRadius = (wallAxis - joinDepth) / cosine;
  const joinY = wallLine + (rearFootOffset * wallScale * joinDepth) / rearRow;
  const rearSlope = (rearFootOffset * wallScale * cosine) / rearRow;
  const normalSpan = joinRadius - frontRadius;
  const closeSpan = frontRadius - closeRadius;
  const normalSlope = (frontY - joinY) / normalSpan;
  const closeSlope = (closeY - frontY) / closeSpan;
  const frontSlope = paintedFloor
    ? normalSlope * frontWalkSlope
    : Math.min(normalSlope * 1.45, closeSlope);

  let groundY: number;
  if (radius >= joinRadius) {
    // Along a row parallel to the north wall, lateral position has no effect.
    const depth = wallAxis - radius * cosine;
    groundY = wallLine + (depth * rearFootOffset * wallScale) / rearRow;
    if (paintedFloor && depth > rearRow) {
      // Join the faster painted-floor slope over the last part of the reference
      // row, preserving its endpoint and keeping the foot moving forward.
      const span = (joinDepth - rearRow) / cosine;
      const progress = (depth - rearRow) / (joinDepth - rearRow);
      const slopeDelta = normalSlope * kitchenWalkSlope - rearSlope;
      groundY += span * slopeDelta * progress ** 5 * (progress - 1);
    }
  } else if (paintedFloor && radius >= frontRadius) {
    const progress = (joinRadius - radius) / normalSpan;
    const row = kitchenFloorRow + walkRowSpan * progress;
    const paintedProgress = (paintedFloorY(row) - kitchenPaintedY) / paintedWalkSpan;
    groundY = joinY + (frontY - joinY) * paintedProgress;
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
