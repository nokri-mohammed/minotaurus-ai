// Canvas drawing only: the maze as an LED dot-matrix panel. Every maze square is one round LED on a
// dark board: walls are lit pale cyan, empty squares are dim, the walked path glows amber, the dot
// is red and the exit is green.
import { FONT_HEIGHT, textLeds } from "./ledFont";
import type { LevelInfo, Point } from "./protocol";

const TRAIL_LENGTH = 40; // squares of the walked path that stay lit, fading out behind the dot
const BOARD = "#05090d";
const OFF = "#0d1820"; // an LED that is not lit
const WALL = "#c4f1ff";
const TRAIL_RGB = "255, 176, 64";
const DOT = "#b8651b"; // brown
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

/**
 * The board is a square of `board` x `board` maze squares, the size of the biggest level, so every
 * level has the same LED size; a smaller maze sits in the middle with unlit LEDs around it.
 */
export function boardSizeFor(levels: LevelInfo[]): number {
  let biggest = 1;
  for (const level of levels) {
    biggest = Math.max(biggest, level.grid.length, level.grid[0].length);
  }
  return biggest;
}

/** Size of one maze square so the board fills `maxWidth` CSS pixels exactly (no gap on the right). */
export function cellSizeFor(board: number, maxWidth: number): number {
  return Math.max(6, maxWidth / board);
}

/** The title strip above the maze: five LEDs of text and one blank LED row under it. */
export const HEADER_LEDS = FONT_HEIGHT + 1;

export function canvasSize(board: number, cell: number): { width: number; height: number } {
  const header = (HEADER_LEDS * cell) / LEDS;
  return { width: board * cell, height: board * cell + header };
}

/** The strip's text: the level's name and its size, e.g. "EASY-01 9X9". */
export function headerText(level: LevelInfo): string {
  return `${level.name} ${level.grid[0].length}x${level.grid.length}`;
}

/** Every maze square is a block of LEDS x LEDS small LEDs. */
export const LEDS = 3;

const FULL = [[1, 1, 1], [1, 1, 1], [1, 1, 1]];
const RING = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]; // 8 LEDs in a ring: the dot
const FLAG = [[1, 1, 1], [1, 1, 0], [1, 0, 0]]; // 6 LEDs: a pole and a pennant, the exit
const CENTRE = [[0, 0, 0], [0, 1, 0], [0, 0, 0]];
const NONE = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];

/** Which of the small LEDs in a square are lit (1) for each kind of square. */
export function ledPattern(kind: CellKind): number[][] {
  if (kind === "wall") return FULL;
  if (kind === "exit") return FLAG;
  if (kind === "dot") return RING;
  if (kind === "trail") return CENTRE;
  return NONE;
}

export function drawArena(
  ctx: CanvasRenderingContext2D,
  level: LevelInfo,
  pos: Point | null,
  trail: Point[],
  cell: number,
  board: number,
): void {
  const { width, height } = canvasSize(board, cell);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = BOARD;
  ctx.fillRect(0, 0, width, height);
  // Unlit LEDs on the whole panel, then the title, then the maze in the middle.
  const step = cell / LEDS;
  for (let row = 0; row < HEADER_LEDS + board * LEDS; row += 1) {
    for (let col = 0; col < board * LEDS; col += 1) {
      drawLed(ctx, col * step, row * step, step, OFF, false);
    }
  }
  drawHeader(ctx, level, board, step);
  const headerHeight = HEADER_LEDS * step;
  const offsetX = Math.floor((board - level.grid[0].length) / 2);
  const offsetY = Math.floor((board - level.grid.length) / 2);
  const rows = screenCells(level, pos, trail);
  for (let y = 0; y < rows.length; y += 1) {
    for (let x = 0; x < rows[y].length; x += 1) {
      drawSquare(ctx, rows[y][x], (x + offsetX) * cell, headerHeight + (y + offsetY) * cell, cell);
    }
  }
}

/** The level's name and size in lit LEDs, one LED in from the left edge; cut off if too long. */
function drawHeader(ctx: CanvasRenderingContext2D, level: LevelInfo, board: number, step: number): void {
  const rows = textLeds(headerText(level));
  const room = board * LEDS - 1;
  for (let row = 0; row < rows.length; row += 1) {
    for (let col = 0; col < rows[row].length && col < room; col += 1) {
      if (rows[row][col] === 1) {
        drawLed(ctx, (col + 1) * step, row * step, step, WALL, true);
      }
    }
  }
}

/** One round LED whose square cell starts at (left, top). */
function drawLed(ctx: CanvasRenderingContext2D, left: number, top: number, step: number, colour: string, on: boolean): void {
  ctx.shadowColor = colour;
  ctx.shadowBlur = on ? step * 0.7 : 0;
  ctx.fillStyle = colour;
  ctx.beginPath();
  ctx.arc(left + step / 2, top + step / 2, step * 0.36, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;
}

/** One maze square as a block of small round LEDs; lit ones glow. */
function drawSquare(ctx: CanvasRenderingContext2D, item: ScreenCell, left: number, top: number, cell: number): void {
  const pattern = ledPattern(item.kind);
  const step = cell / LEDS;
  const lit = colourOf(item);
  for (let row = 0; row < LEDS; row += 1) {
    for (let col = 0; col < LEDS; col += 1) {
      const on = pattern[row][col] === 1;
      drawLed(ctx, left + col * step, top + row * step, step, on ? lit : OFF, on);
    }
  }
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
