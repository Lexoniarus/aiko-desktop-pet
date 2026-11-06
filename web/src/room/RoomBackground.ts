import { roomPresentation } from './RoomPresentation';

/** Assemble unchanged v16 art at its authored height and floor seam. */
export function roomBackground(
  source: HTMLImageElement,
  floor: HTMLImageElement,
  window: boolean,
  mirroredFloor: boolean,
): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = roomPresentation.panelWidth;
  canvas.height = roomPresentation.designHeight;
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
  if (window) {
    // The reference's wall-only colour match excludes the window and curtains.
    ctx.fillStyle = 'rgba(255, 243, 252, 0.33)';
    for (const region of [
      [0, 0, 1800, 38],
      [20, 65, 185, 690],
      [1125, 65, 675, 240],
      [1125, 305, 310, 170],
      [1580, 305, 220, 170],
      [1125, 475, 675, 280],
    ]) {
      ctx.fillRect(region[0]!, region[1]!, region[2]!, region[3]!);
    }
  }
  ctx.drawImage(
    floor,
    0,
    (floor.height * 760) / 900,
    floor.width,
    (floor.height * 42) / 900,
    0,
    760,
    1800,
    42,
  );
  if (window) {
    const foot = document.createElement('canvas');
    foot.width = 1800;
    foot.height = 42;
    const windowContext = foot.getContext('2d')!;
    windowContext.drawImage(
      source,
      0,
      (source.height * 760) / 900,
      source.width,
      (source.height * 42) / 900,
      0,
      0,
      1800,
      42,
    );
    const pixels = windowContext.getImageData(0, 0, 1800, 42);
    for (let i = 0; i < pixels.data.length; i += 4) {
      const r = pixels.data[i]!,
        g = pixels.data[i + 1]!,
        b = pixels.data[i + 2]!;
      if (g < r + 4 || b < r + 8) pixels.data[i + 3] = 0;
    }
    windowContext.putImageData(pixels, 0, 0);
    ctx.drawImage(foot, 0, 760);
  }
  ctx.save();
  if (mirroredFloor) {
    ctx.translate(1800, 0);
    ctx.scale(-1, 1);
  }
  ctx.drawImage(
    floor,
    0,
    (floor.height * 802) / 900,
    floor.width,
    (floor.height * 98) / 900,
    0,
    802,
    1800,
    98,
  );
  ctx.restore();
  // Equal-width joint covers keep all four boundaries level and recognisable.
  ctx.fillStyle = '#e7e3f0';
  ctx.strokeStyle = '#a1abc6';
  ctx.lineWidth = 2;
  for (const x of [0, 1800]) {
    ctx.fillRect(x - 18, 53, 36, 749);
    ctx.strokeRect(x - 18, 53, 36, 749);
  }
  return canvas;
}
