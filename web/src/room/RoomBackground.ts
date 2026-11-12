import { roomPresentation } from './RoomPresentation';

/** The panorama uses the wall part of the v16 art. */
export function roomBackground(
  source: HTMLImageElement,
  window: boolean,
): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = roomPresentation.panelWidth;
  canvas.height = 760;
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(
    source,
    0,
    0,
    source.width,
    (source.height * canvas.height) / roomPresentation.designHeight,
    0,
    0,
    canvas.width,
    canvas.height,
  );
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
  return canvas;
}
