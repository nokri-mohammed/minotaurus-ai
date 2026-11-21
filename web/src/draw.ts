// Canvas drawing only: the maze, the exit, a fading trail and the dot.
import type { LevelInfo, Point } from "./protocol";

const TRAIL_LENGTH = 12;
const INK = "#141414";
const WALL = "#d5d9e0";
const FLOOR = "#ffffff";
const HUE = "#1d5fbf"; // the one data hue: the dot and its trail


/** Whole-pixel cell size that fits `maxWidth` CSS pixels, so edges stay sharp. */
export function cellSizeFor(level: LevelInfo, maxWidth: number): number {
  return Math.max(8, Math.floor(maxWidth / level.grid[0].length));
}

export function canvasSize(level: LevelInfo, cell: number): { width: number; height: number } {
  return { width: level.grid[0].length * cell, height: level.grid.length * cell };
}

export function drawArena(
  ctx: CanvasRenderingContext2D,
  level: LevelInfo,
  pos: Point | null,
  trail: Point[],
  CELL: number,
): void {
  const { width, height } = canvasSize(level, CELL);
  ctx.clearRect(0, 0, width, height);
  level.grid.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      ctx.fillStyle = ch === "#" ? WALL : FLOOR;
      ctx.fillRect(x * CELL, y * CELL, CELL, CELL);
    });
  });
  const [ex, ey] = exitOf(level);
  ctx.strokeStyle = INK;
  ctx.lineWidth = Math.max(2, CELL / 11);
  ctx.beginPath();
  ctx.arc(ex * CELL + CELL / 2, ey * CELL + CELL / 2, CELL * 0.3, 0, Math.PI * 2);
  ctx.stroke();
  const recent = trail.slice(-TRAIL_LENGTH);
  recent.forEach((p, i) => {
    ctx.fillStyle = `rgba(29, 95, 191, ${((i + 1) / (recent.length + 1)) * 0.4})`;
    const pad = CELL * 0.19;
    ctx.fillRect(p.x * CELL + pad, p.y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad);
  });
  const dot = pos ?? startOf(level);
  if (dot) {
    ctx.fillStyle = HUE;
    ctx.beginPath();
    ctx.arc(dot.x * CELL + CELL / 2, dot.y * CELL + CELL / 2, CELL * 0.32, 0, Math.PI * 2);
    ctx.fill();
  }
}

function exitOf(level: LevelInfo): [number, number] {
  for (let y = 0; y < level.grid.length; y++) {
    const x = level.grid[y].indexOf("E");
    if (x >= 0) return [x, y];
  }
  return [-1, -1];
}

function startOf(level: LevelInfo): Point | null {
  for (let y = 0; y < level.grid.length; y++) {
    const x = level.grid[y].indexOf("S");
    if (x >= 0) return { x, y };
  }
  return null;
}
