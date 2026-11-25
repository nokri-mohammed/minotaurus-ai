import { useEffect, useRef, useState, type ReactNode } from "react";
import { boardSizeFor, canvasSize, cellSizeFor, drawArena, HEADER_LEDS, LEDS } from "../draw";
import type { LevelInfo, Point } from "../protocol";

type Props = {
  level: LevelInfo | null;
  levels: LevelInfo[];
  pos: Point | null;
  trail: Point[];
  /** shown inside the screen, at the right end of the title strip (the run button) */
  action?: ReactNode;
};

const MAX = 4000; // no cap: the board fills its container

/** Draws at the real display size times the pixel ratio, so circles and edges stay crisp. */
export function MazeCanvas({ level, levels, pos, trail, action }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const ref = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(560);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const update = () => setWidth(Math.min(MAX, Math.floor(el.clientWidth)));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const board = boardSizeFor(levels);
  const cell = level ? cellSizeFor(board, width) : 0;
  const size = level ? canvasSize(board, cell) : { width: 0, height: 0 };

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || !level) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(size.width * dpr);
    canvas.height = Math.round(size.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawArena(ctx, level, pos, trail, cell, board);
  }, [level, pos, trail, cell, board, size.width, size.height]);

  const stripHeight = (HEADER_LEDS * cell) / LEDS;
  return (
    <div ref={wrap} className="maze-wrap relative">
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
      {level && action && (
        <div className="absolute top-0 right-2 flex items-center" style={{ height: stripHeight }}>
          {action}
        </div>
      )}
    </div>
  );
}
