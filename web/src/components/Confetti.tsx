import { useEffect, useRef } from "react";
import { type Piece, makePieces, stepPieces } from "../confetti";

type Props = { burst: number }; // a counter: every time it goes up, one burst plays

const PIECES = 140;
const MAX_SECONDS = 4;

function drawPieces(ctx: CanvasRenderingContext2D, pieces: Piece[]) {
  for (const piece of pieces) {
    ctx.save();
    ctx.translate(piece.x, piece.y);
    ctx.rotate(piece.rotation);
    ctx.fillStyle = piece.color;
    ctx.fillRect(-piece.size / 2, -piece.size / 4, piece.size, piece.size / 2);
    ctx.restore();
  }
}

/** One short burst of confetti over the whole page. It never takes clicks and is skipped when the
 *  player prefers reduced motion. */
export function Confetti({ burst }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (burst === 0 || !canvas || !ctx) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const dpr = window.devicePixelRatio || 1;
    const width = window.innerWidth;
    const height = window.innerHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    let pieces = makePieces(PIECES, width);
    let last = performance.now();
    let elapsed = 0;
    let frame = 0;

    function tick(now: number) {
      const seconds = Math.min(0.05, (now - last) / 1000);
      last = now;
      elapsed += seconds;
      pieces = stepPieces(pieces, seconds, height);
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx!.clearRect(0, 0, width, height);
      drawPieces(ctx!, pieces);
      if (pieces.length > 0 && elapsed < MAX_SECONDS) {
        frame = requestAnimationFrame(tick);
      } else {
        ctx!.clearRect(0, 0, width, height);
      }
    }

    frame = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [burst]);

  return <canvas ref={ref} className="confetti" aria-hidden="true" />;
}
