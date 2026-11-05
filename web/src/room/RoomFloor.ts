/** One continuous floor across all wall panels, including the panorama wrap. */
export function paintRoomFloor(
  ctx: CanvasRenderingContext2D,
  source: HTMLImageElement,
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
  ctx.fillStyle = '#eee4e6';
  ctx.fillRect(0, 782, 5100, 16);
  ctx.fillStyle = '#8a6059';
  ctx.fillRect(0, 782, 5100, 4);
  ctx.fillStyle = '#a87868';
  ctx.fillRect(0, 798, 5100, 4);
}
