import { useEffect, useRef, useState } from "react";
import { boardSizeFor, canvasSize, cellSizeFor, drawArena, hitsAction } from "../draw";
import type { LevelInfo, Point } from "../protocol";

type Props = {
  level: LevelInfo | null;
  levels: LevelInfo[];
  pos: Point | null;
  trail: Point[];
  /** the run button, drawn in LEDs at the right end of the title strip */
  action?: { label: string; stop: boolean; enabled: boolean; onClick: () => void };
};

const MAX = 4000; // no cap: the board fills its container

/** Draws at the real display size times the pixel ratio, so circles and edges stay crisp. */
export function MazeCanvas({ level, levels, pos, trail, action }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const ref = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(560);
  const [hover, setHover] = useState(false);

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
    let panelAction = null;
    if (action) {
      panelAction = { label: action.label, stop: action.stop, enabled: action.enabled, hover };
    }
    drawArena(ctx, level, pos, trail, cell, board, panelAction);
  }, [level, pos, trail, cell, board, size.width, size.height, action?.label, action?.stop, action?.enabled, hover]);

  function overButton(event: React.MouseEvent<HTMLCanvasElement>): boolean {
    if (!action) return false;
    const box = event.currentTarget.getBoundingClientRect();
    return hitsAction(board, action.label, cell, event.clientX - box.left, event.clientY - box.top);
  }

  return (
    <div ref={wrap} className="maze-wrap">
      {level ? (
        <canvas
          ref={ref}
          className="maze"
          style={{ width: size.width, height: size.height, cursor: hover && action?.enabled ? "pointer" : "default" }}
          onMouseMove={(event) => setHover(overButton(event))}
          onMouseLeave={() => setHover(false)}
          onClick={(event) => {
            if (action && action.enabled && overButton(event)) action.onClick();
          }}
          aria-label={`Maze ${level.name} with the dot`}
        />
      ) : (
        <div className="maze-empty">No level loaded.</div>
      )}
      {level && action && (
        <button type="button" className="sr-only" disabled={!action.enabled} onClick={action.onClick}>
          {action.stop ? "Stop run" : "Start run"}
        </button>
      )}
    </div>
  );
}
