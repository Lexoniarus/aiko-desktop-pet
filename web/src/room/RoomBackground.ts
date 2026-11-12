import { roomPresentation } from './RoomPresentation';

type ImageRect = [x: number, y: number, width: number, height: number];

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
