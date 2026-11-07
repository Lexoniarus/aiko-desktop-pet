/** One authored board space for previews, held chips, flight and settled pieces. */
export const connectFourGeometry = {
  size: 480,
  margin: 100,
  cell: 40,
  rows: 6,
  columns: 7,
  top: 112,
  entry: 92,
  base: 446,
  chip: 32,
} as const;

export interface TableGameFrame {
  x: number;
  y: number;
  scale: number;
  chip: number;
  playerX: number;
  playerY: number;
}

export function tableGameFrame(table: {
  x: number;
  y: number;
  width: number;
  height: number;
}): TableGameFrame {
  const scale = (table.width * 0.9) / connectFourGeometry.size;
  const surface = table.y - table.height * 0.88;
  return {
    x: table.x - (connectFourGeometry.size * scale) / 2,
    y: surface - connectFourGeometry.base * scale,
    scale,
    chip: connectFourGeometry.chip * scale,
    playerX: table.x - table.width * 0.34,
    playerY: surface + table.height * 0.2,
  };
}

export function columnAt(x: number): number | undefined {
  const column = Math.floor(
    (x - connectFourGeometry.margin) / connectFourGeometry.cell,
  );
  return column >= 0 && column < connectFourGeometry.columns ? column : undefined;
}

export function landingCell(
  cells: readonly unknown[],
  column: number,
): number | undefined {
  for (let row = connectFourGeometry.rows - 1; row >= 0; row--) {
    const cell = row * connectFourGeometry.columns + column;
    if (cells[cell] === 0) return cell;
  }
  return undefined;
}

export function cellPoint(cell: number): { x: number; y: number } {
  return {
    x:
      connectFourGeometry.margin +
      ((cell % connectFourGeometry.columns) + 0.5) * connectFourGeometry.cell,
    y:
      connectFourGeometry.top +
      (Math.floor(cell / connectFourGeometry.columns) + 0.5) * connectFourGeometry.cell,
  };
}

/** Continuous centre trajectory; diameter never changes during the handoff. */
export function chipPoint(
  start: { x: number; y: number },
  cell: number,
  fraction: number,
  flightFraction: number,
): { x: number; y: number } {
  const g = connectFourGeometry;
  const target = { x: cellPoint(cell).x, y: g.entry };
  let height = Math.abs(target.y - start.y) * 0.55 + 60;
  if (start.x < g.margin || start.x > g.margin + 7 * g.cell) {
    for (let i = 1; i < 100; i++) {
      const t = i / 100;
      const x = start.x + (target.x - start.x) * t;
      if (x + g.chip / 2 >= g.margin && x - g.chip / 2 <= g.margin + 7 * g.cell)
        height = Math.max(
          height,
          (start.y + (target.y - start.y) * t + g.chip / 2 - g.top + 14 * (1 - t)) /
            (4 * t * (1 - t)),
        );
    }
  }
  if (fraction < flightFraction) {
    const t = Math.max(0, fraction / flightFraction);
    return {
      x: start.x + (target.x - start.x) * t,
      y: start.y + (target.y - start.y) * t - 4 * height * t * (1 - t),
    };
  }
  const t = Math.min(1, (fraction - flightFraction) / (1 - flightFraction));
  return { x: target.x, y: target.y + (cellPoint(cell).y - target.y) * t * t };
}
