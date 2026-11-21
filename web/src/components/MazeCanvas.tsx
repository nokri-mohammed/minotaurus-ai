import { useEffect, useRef, useState } from "react";
import { canvasSize, cellSizeFor, drawArena } from "../draw";
import type { LevelInfo, Point } from "../protocol";

type Props = { level: LevelInfo | null; pos: Point | null; trail: Point[] };

const MAX = 480;

/** Draws at the real display size times the pixel ratio, so circles and edges stay crisp. */
export function MazeCanvas({ level, pos, trail }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const ref = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(MAX);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const update = () => setWidth(Math.min(MAX, Math.floor(el.clientWidth)));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const cell = level ? cellSizeFor(level, width) : 0;
  const size = level ? canvasSize(level, cell) : { width: 0, height: 0 };

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || !level) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(size.width * dpr);
    canvas.height = Math.round(size.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawArena(ctx, level, pos, trail, cell);
  }, [level, pos, trail, cell, size.width, size.height]);

  return (
    <div ref={wrap} className="maze-wrap">
      {level ? (
        <canvas
          ref={ref}
          className="maze"
          style={{ width: size.width, height: size.height }}
          aria-label={`Maze ${level.name} with the dot`}
        />
      ) : (
        <div className="maze-empty">No level loaded.</div>
      )}
    </div>
  );
}
