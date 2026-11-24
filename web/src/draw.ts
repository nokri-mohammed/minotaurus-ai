// Canvas drawing only: the maze as an LED dot-matrix panel. Every maze square is one round LED on a
// dark board: walls are lit pale cyan, empty squares are dim, the walked path glows amber, the dot
// is red and the exit is green.
import type { LevelInfo, Point } from "./protocol";

const TRAIL_LENGTH = 40; // squares of the walked path that stay lit, fading out behind the dot
const BOARD = "#05090d";
const OFF = "#0d1820"; // an LED that is not lit
const WALL = "#c4f1ff";
const TRAIL_RGB = "255, 176, 64";
const DOT = "#ff3b30";
const EXIT = "#2eea6b";

export type CellKind = "wall" | "floor" | "trail" | "dot" | "exit" | "start";
export type ScreenCell = { kind: CellKind; fade: number }; // fade 0..1, only for the trail

/**
 * What the panel shows, one cell per maze square. The dot is drawn over the trail, the trail over
 * the floor. `trail` is the squares visited before the dot, oldest first.
 */
export function screenCells(level: LevelInfo, pos: Point | null, trail: Point[]): ScreenCell[][] {
  const rows: ScreenCell[][] = [];
  for (let y = 0; y < level.grid.length; y += 1) {
    const row: ScreenCell[] = [];
    for (let x = 0; x < level.grid[y].length; x += 1) {
      const letter = level.grid[y][x];
      let kind: CellKind = "floor";
      if (letter === "#") kind = "wall";
      if (letter === "E") kind = "exit";
      if (letter === "S") kind = "start";
      row.push({ kind, fade: 0 });
    }
    rows.push(row);
  }
  const recent = trail.slice(-TRAIL_LENGTH);
  for (let i = 0; i < recent.length; i += 1) {
    const cell = rows[recent[i].y]?.[recent[i].x];
    if (!cell || cell.kind === "wall" || cell.kind === "exit") continue;
    cell.kind = "trail";
    cell.fade = (i + 1) / recent.length; // newer is brighter; a square walked again keeps its newest age
  }
  const dot = pos ?? startOf(level);
  const here = dot ? rows[dot.y]?.[dot.x] : undefined;
  if (here) {
    here.kind = "dot";
  }
  return rows;
}

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
  cell: number,
): void {
  const { width, height } = canvasSize(level, cell);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = BOARD;
  ctx.fillRect(0, 0, width, height);
  const rows = screenCells(level, pos, trail);
  for (let y = 0; y < rows.length; y += 1) {
    for (let x = 0; x < rows[y].length; x += 1) {
      drawLed(ctx, rows[y][x], x * cell + cell / 2, y * cell + cell / 2, cell);
    }
  }
}

/** One LED: a round dot, with a soft glow when it is lit. */
function drawLed(ctx: CanvasRenderingContext2D, item: ScreenCell, cx: number, cy: number, cell: number): void {
  const lit = item.kind !== "floor" && item.kind !== "start";
  const colour = colourOf(item);
  ctx.shadowColor = colour;
  ctx.shadowBlur = lit ? cell * 0.45 : 0;
  ctx.fillStyle = colour;
  ctx.beginPath();
  ctx.arc(cx, cy, cell * (item.kind === "dot" ? 0.4 : 0.32), 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;
}

function colourOf(item: ScreenCell): string {
  if (item.kind === "wall") return WALL;
  if (item.kind === "dot") return DOT;
  if (item.kind === "exit") return EXIT;
  if (item.kind === "trail") return `rgba(${TRAIL_RGB}, ${0.3 + item.fade * 0.7})`;
  return OFF;
}

function startOf(level: LevelInfo): Point | null {
  for (let y = 0; y < level.grid.length; y += 1) {
    const x = level.grid[y].indexOf("S");
    if (x >= 0) return { x, y };
  }
  return null;
}
