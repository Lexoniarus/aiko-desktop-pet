import { roomPresentation } from './RoomPresentation';
import { floorArtwork } from './RoomDepthCurve';

type ImageRect = [x: number, y: number, width: number, height: number];

/** Prepare a half-turn repeat with identical pixels at either end. */
export function roomFloorTexture(source: HTMLImageElement): HTMLCanvasElement {
  const { sourceRows, displayRows } = floorArtwork;
  const width = Math.min(source.naturalWidth, 1600);
  const canvas = document.createElement('canvas');
  canvas.width = width * 2;
  canvas.height = displayRows.at(-1)! * 2;
  const context = canvas.getContext('2d')!;
  const scale = source.naturalHeight / sourceRows.at(-1)!;
  for (let row = 0; row < sourceRows.length - 1; row++) {
    const top = sourceRows[row]!;
    const displayTop = displayRows[row]!;
    context.drawImage(
      source,
      0,
      top * scale,
      source.naturalWidth,
      (sourceRows[row + 1]! - top) * scale,
      0,
      displayTop * 2,
      width,
      (displayRows[row + 1]! - displayTop) * 2,
    );
  }
  context.translate(canvas.width, 0);
  context.scale(-1, 1);
  context.drawImage(canvas, 0, 0, width, canvas.height, 0, 0, width, canvas.height);
  return canvas;
}

function drawReferenceRegion(
  ctx: CanvasRenderingContext2D,
  source: HTMLImageElement,
  [x, y, width, height]: ImageRect,
  target: ImageRect,
): void {
  const scaleX = source.naturalWidth / 1774;
  const scaleY = source.naturalHeight / 887;
  ctx.drawImage(
    source,
    x * scaleX,
    y * scaleY,
    width * scaleX,
    height * scaleY,
    ...target,
  );
}

/** Assemble frontal wall strips from the v16 art. */
export function roomBackground(
  source: HTMLImageElement,
  windowSource?: HTMLImageElement,
): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = roomPresentation.panelWidth;
  canvas.height = 760;
  const ctx = canvas.getContext('2d')!;
  const { width, height } = canvas;
  drawReferenceRegion(ctx, source, [32, 75, 1700, 650], [0, 0, width, height]);
  if (windowSource) {
    ctx.fillStyle = 'rgba(255, 243, 252, 0.25)';
    ctx.fillRect(0, 0, width, height);
    const windowWidth = width * 0.44;
    const windowHeight = (height * 2) / 3;
    const x = width * 0.39 - windowWidth / 2;
    const y = height / 6;
    // Keep the rod and curtain edges, then cap the glass above the old balcony.
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(
      x + windowWidth * 0.014,
      y,
      windowWidth * 0.972,
      windowHeight * 0.05,
      3,
    );
    ctx.rect(
      x + windowWidth * 0.014,
      y + windowHeight * 0.04,
      windowWidth * 0.897,
      windowHeight * 0.96,
    );
    ctx.clip();
    drawReferenceRegion(
      ctx,
      windowSource,
      [196, 57, 1010, 586],
      [x, y, windowWidth, windowHeight],
    );
    ctx.restore();
    ctx.fillStyle = '#b29eb9';
    ctx.fillRect(x, y + windowHeight - 3, windowWidth * 0.93, 11);
    ctx.fillStyle = '#d9c7da';
    ctx.fillRect(x, y + windowHeight - 3, windowWidth * 0.93, 4);
    drawReferenceRegion(
      ctx,
      windowSource,
      [1418, 292, 144, 172],
      [width * 0.8, height * 0.36, width * 0.08, height * 0.22],
    );
  }
  ctx.fillStyle = '#9ca0bc';
  ctx.fillRect(0, height * 0.047, width, height * 0.013);
  return canvas;
}
