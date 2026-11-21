import { useEffect, useRef } from "react";
import { canvasSize, drawArena } from "../draw";
import type { LevelInfo, Point } from "../protocol";

type Props = { level: LevelInfo | null; pos: Point | null; trail: Point[] };

export function MazeCanvas({ level, pos, trail }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (ctx && level) drawArena(ctx, level, pos, trail);
  }, [level, pos, trail]);
  if (!level) return <div className="maze maze-empty">No level loaded.</div>;
  const { width, height } = canvasSize(level);
  return <canvas ref={ref} className="maze" width={width} height={height} aria-label={`Maze ${level.name} with the dot`} />;
}
