/** One continuous floor across all wall panels, including the panorama wrap. */
export function paintRoomFloor(
  ctx: CanvasRenderingContext2D,
  source: HTMLImageElement,
  living: HTMLImageElement,
): void {
  // The two reference backgrounds have different skirting heights/plank grids.
  // Reuse the kitchen floor, rather than joining those unrelated perspective
  // grids at room boundaries. Mirrored repeats share their exact border pixels.
  const strip = 1275;
  for (let index = 0; index < 4; index++) {
    ctx.save();
    ctx.translate((index + (index % 2)) * strip, 0);
    ctx.scale(index % 2 ? -1 : 1, 1);
    ctx.drawImage(
      source,
      0,
      (source.height * 802) / 900,
      source.width,
      (source.height * 98) / 900,
      0,
      802,
      strip,
      98,
    );
    ctx.restore();
  }
  // One uninterrupted skirting behind the balcony. Restore only its original
  // blue/teal frame and curtain pixels, rather than leaving a rectangular gap
  // whose guessed edges produce visible steps in the wall beside the window.
  ctx.fillStyle = '#eee4e6';
  ctx.fillRect(0, 760, 5100, 42);
  ctx.fillStyle = '#8a6059';
  ctx.fillRect(0, 766, 5100, 4);
  ctx.fillStyle = '#a87868';
  ctx.fillRect(0, 798, 5100, 4);
  const foot = document.createElement('canvas');
  foot.width = 1800;
  foot.height = 42;
  const windowContext = foot.getContext('2d')!;
  windowContext.drawImage(
    living,
    0,
    (living.height * 760) / 900,
    living.width,
    (living.height * 42) / 900,
    0,
    0,
    1800,
    42,
  );
  const pixels = windowContext.getImageData(0, 0, 1800, 42);
  for (let i = 0; i < pixels.data.length; i += 4) {
    const [r, g, b] = [pixels.data[i]!, pixels.data[i + 1]!, pixels.data[i + 2]!];
    if (g < r + 4 || b < r + 8) pixels.data[i + 3] = 0;
  }
  windowContext.putImageData(pixels, 0, 0);
  ctx.drawImage(foot, 1800, 760);
}
