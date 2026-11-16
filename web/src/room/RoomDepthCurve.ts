/** Screen measurements from the accepted kitchen walk and close-call previews. */
export const depthReferenceHeight = 544;
export const closeCrop = 0.26;
const kitchenY = 319.3672661654135;
const frontY = 473.2372225428042;
const kitchenSpriteHeight = 212.73235099514345;
const closeSpriteHeight = 486.2521125;
const closeY = depthReferenceHeight + closeCrop * closeSpriteHeight;

/** Source and projected seam heights, measured in the accepted floor preview. */
export const floorArtwork = {
  sourceRows: [0, 26, 60, 101, 147, 201, 262, 333, 417, 511, 616, 724],
  displayRows: [0, 16, 34, 54, 74, 96, 120, 145, 173, 203, 235, 268],
} as const;

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

export class RoomDepthCurve {
  readonly floorY: number;
  private readonly farRadius: number;
  private readonly frontRadius: number;
  private readonly closeRadius: number;
  private readonly kitchenRadius = 200;
  private readonly rearSpan: number;
  private readonly walkSpan: number;
  private readonly rearRise: number;
  private readonly rearExponent: number;
  private readonly closeSpan: number;
  private readonly frontSlope: number;

  constructor(
    farRadius: number,
    frontRadius: number,
    closeRadius: number,
    floorY: number,
  ) {
    this.farRadius = farRadius;
    this.frontRadius = frontRadius;
    this.closeRadius = closeRadius;
    this.floorY = floorY;
    this.walkSpan = this.kitchenRadius - frontRadius;
    this.rearSpan = farRadius - this.kitchenRadius;
    this.rearRise = kitchenY - floorY;
    this.closeSpan = frontRadius - closeRadius;
    const walkSlope = (frontY - kitchenY) / this.walkSpan;
    // A linear term makes every rear floor row invertible. The power term
    // matches the steeper tangent at the beginning of the approved walk.
    this.rearExponent =
      (2 * walkSlope * kitchenWalkSlope * this.rearSpan) / this.rearRise - 1;
    this.frontSlope = walkSlope * frontWalkSlope;
  }

  at(radius: number): { groundY: number; spriteHeight: number } {
    let groundY: number;
    if (radius >= this.kitchenRadius) {
      const t = Math.max(0, (this.farRadius - radius) / this.rearSpan);
      groundY = this.floorY + (this.rearRise * (t + t ** this.rearExponent)) / 2;
    } else if (radius >= this.frontRadius) {
      const progress = (this.kitchenRadius - radius) / this.walkSpan;
      const row = kitchenFloorRow + walkRowSpan * progress;
      const paintedProgress = (paintedFloorY(row) - kitchenPaintedY) / paintedWalkSpan;
      groundY = kitchenY + (frontY - kitchenY) * paintedProgress;
    } else {
      groundY = floorCurve(
        frontY,
        closeY,
        this.closeSpan,
        this.frontRadius - Math.max(this.closeRadius, radius),
        this.frontSlope,
        ((closeY - frontY) / this.closeSpan) * 1.35,
      );
    }
    const growth = (groundY - kitchenY) / (closeY - kitchenY);
    return {
      groundY,
      spriteHeight:
        kitchenSpriteHeight + (closeSpriteHeight - kitchenSpriteHeight) * growth,
    };
  }
}
