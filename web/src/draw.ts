// Canvas drawing only: the maze, the exit, a fading trail and the dot.
import type { LevelInfo, Point } from "./protocol";

const TRAIL_LENGTH = 40; // squares of the walked path that stay visible, fading out behind the dot
const INK = "#141414";
const FLOOR = "#ffffff";
const HUE = "#0f8b6d"; // the one data hue (also --data in style.css): the dot and its trail
const HUE_RGB = "15, 139, 109";


export type Segment = { x1: number; y1: number; x2: number; y2: number };

/**
 * The walls as thin lines. Each wall cell is a point; two wall cells that touch (right or below)
 * are joined by one line. A wall cell with no wall neighbour is a lone post. Coordinates are in
 * cells, at the centre of each cell. A gap in a wall (the exit in the outer wall) stays a gap.
 */
export function wallLines(grid: string[]): { segments: Segment[]; posts: Point[] } {
  const segments: Segment[] = [];
  const posts: Point[] = [];
  const isWall = (x: number, y: number): boolean => grid[y]?.[x] === "#";

  for (let y = 0; y < grid.length; y += 1) {
    for (let x = 0; x < grid[y].length; x += 1) {
      if (!isWall(x, y)) continue;
      const hasRight = isWall(x + 1, y);
      const hasBelow = isWall(x, y + 1);
      if (hasRight) segments.push({ x1: x, y1: y, x2: x + 1, y2: y });
      if (hasBelow) segments.push({ x1: x, y1: y, x2: x, y2: y + 1 });
      const hasLeft = isWall(x - 1, y);
      const hasAbove = isWall(x, y - 1);
      if (!hasRight && !hasBelow && !hasLeft && !hasAbove) posts.push({ x, y });
    }
  }
  return { segments, posts };
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
  CELL: number,
): void {
  const { width, height } = canvasSize(level, CELL);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = FLOOR;
  ctx.fillRect(0, 0, width, height);
  drawWalls(ctx, level, CELL);
  const [ex, ey] = exitOf(level);
  drawFlag(ctx, ex * CELL, ey * CELL, CELL);
  const dot = pos ?? startOf(level);
  drawTrail(ctx, trail, dot, CELL);
  if (dot) drawDot(ctx, dot, CELL);
}

/** The walked path as a soft line that fades behind the dot. A bump (same square twice) draws nothing. */
function drawTrail(ctx: CanvasRenderingContext2D, trail: Point[], dot: Point | null, cell: number): void {
  const recent = trail.slice(-TRAIL_LENGTH);
  if (dot) recent.push(dot);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(2, cell * 0.16);
  for (let i = 1; i < recent.length; i += 1) {
    const from = recent[i - 1];
    const to = recent[i];
    if (from.x === to.x && from.y === to.y) continue;
    const fade = i / recent.length;
    ctx.strokeStyle = `rgba(${HUE_RGB}, ${0.12 + fade * 0.5})`;
    ctx.beginPath();
    ctx.moveTo(from.x * cell + cell / 2, from.y * cell + cell / 2);
    ctx.lineTo(to.x * cell + cell / 2, to.y * cell + cell / 2);
    ctx.stroke();
  }
}

/** The dot: a soft halo, a white edge and the data hue. */
function drawDot(ctx: CanvasRenderingContext2D, dot: Point, cell: number): void {
  const cx = dot.x * cell + cell / 2;
  const cy = dot.y * cell + cell / 2;
  ctx.fillStyle = `rgba(${HUE_RGB}, 0.18)`;
  ctx.beginPath();
  ctx.arc(cx, cy, cell * 0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = HUE;
  ctx.strokeStyle = FLOOR;
  ctx.lineWidth = Math.max(1.5, cell * 0.06);
  ctx.beginPath();
  ctx.arc(cx, cy, cell * 0.24, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
}

/** Thin ink lines for the walls, like a drawn maze. An even width on whole-pixel centres stays sharp. */
function drawWalls(ctx: CanvasRenderingContext2D, level: LevelInfo, cell: number): void {
  const { segments, posts } = wallLines(level.grid);
  const lineWidth = Math.max(2, 2 * Math.round(cell * 0.045));
  const centre = (n: number): number => Math.round(n * cell + cell / 2);

  ctx.strokeStyle = INK;
  ctx.fillStyle = INK;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "square";
  ctx.beginPath();
  for (const s of segments) {
    ctx.moveTo(centre(s.x1), centre(s.y1));
    ctx.lineTo(centre(s.x2), centre(s.y2));
  }
  ctx.stroke();
  for (const post of posts) {
    ctx.fillRect(centre(post.x) - lineWidth / 2, centre(post.y) - lineWidth / 2, lineWidth, lineWidth);
  }
}

/** The exit: an ink flag on a pole, inside the square at (x, y) pixels. */
function drawFlag(ctx: CanvasRenderingContext2D, x: number, y: number, cell: number): void {
  const poleX = x + cell * 0.34;
  const top = y + cell * 0.16;
  const bottom = y + cell * 0.84;
  ctx.fillStyle = INK;
  ctx.fillRect(poleX - Math.max(1, cell * 0.045), top, Math.max(2, cell * 0.09), bottom - top);
  ctx.beginPath();
  ctx.moveTo(poleX, top);
  ctx.lineTo(x + cell * 0.82, top + cell * 0.2);
  ctx.lineTo(poleX, top + cell * 0.4);
  ctx.closePath();
  ctx.fill();
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
