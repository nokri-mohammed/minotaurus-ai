// Canvas drawing only: the maze, the exit, a fading trail and the dot.
import type { LevelInfo, Point } from "./protocol";

export const CELL = 32;
const TRAIL_LENGTH = 12;

export function canvasSize(level: LevelInfo): { width: number; height: number } {
  return { width: level.grid[0].length * CELL, height: level.grid.length * CELL };
}

export function drawArena(
  ctx: CanvasRenderingContext2D,
  level: LevelInfo,
  pos: Point | null,
  trail: Point[],
): void {
  const { width, height } = canvasSize(level);
  ctx.clearRect(0, 0, width, height);
  level.grid.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      ctx.fillStyle = ch === "#" ? "#2b2f3a" : ch === "E" ? "#3fa66b" : "#f3efe6";
      ctx.fillRect(x * CELL, y * CELL, CELL, CELL);
    });
  });
  const recent = trail.slice(-TRAIL_LENGTH);
  recent.forEach((p, i) => {
    ctx.fillStyle = `rgba(224, 112, 48, ${((i + 1) / (recent.length + 1)) * 0.5})`;
    ctx.fillRect(p.x * CELL + 6, p.y * CELL + 6, CELL - 12, CELL - 12);
  });
  const dot = pos ?? startOf(level);
  if (dot) {
    ctx.fillStyle = "#e07030";
    ctx.beginPath();
    ctx.arc(dot.x * CELL + CELL / 2, dot.y * CELL + CELL / 2, CELL * 0.32, 0, Math.PI * 2);
    ctx.fill();
  }
}

function startOf(level: LevelInfo): Point | null {
  for (let y = 0; y < level.grid.length; y++) {
    const x = level.grid[y].indexOf("S");
    if (x >= 0) return { x, y };
  }
  return null;
}
