// Confetti: pure functions for the pieces. The component draws them; nothing here touches the page.

export type Piece = {
  x: number;
  y: number;
  vx: number; // pixels per second, sideways
  vy: number; // pixels per second, downwards
  size: number;
  rotation: number; // radians
  spin: number; // radians per second
  color: string;
};

export const CONFETTI_COLORS = ["#1d5fbf", "#e5484d", "#f5a524", "#30a46c", "#8e4ec6", "#141414"];

const GRAVITY = 600; // pixels per second, per second

/** `count` pieces, spread across `width`, just above the top edge. `random` gives 0 up to 1. */
export function makePieces(count: number, width: number, random: () => number = Math.random): Piece[] {
  const pieces: Piece[] = [];
  for (let i = 0; i < count; i += 1) {
    const colorIndex = Math.min(CONFETTI_COLORS.length - 1, Math.floor(random() * CONFETTI_COLORS.length));
    pieces.push({
      x: random() * width,
      y: -random() * 20,
      vx: (random() - 0.5) * 200,
      vy: 100 + random() * 200,
      size: 6 + random() * 6,
      rotation: random() * Math.PI * 2,
      spin: (random() - 0.5) * 10,
      color: CONFETTI_COLORS[colorIndex],
    });
  }
  return pieces;
}

/** Move every piece forward by `seconds`. Pieces below `height` are dropped. Returns a new list. */
export function stepPieces(pieces: Piece[], seconds: number, height: number): Piece[] {
  const moved: Piece[] = [];
  for (const piece of pieces) {
    const vy = piece.vy + GRAVITY * seconds;
    const next: Piece = {
      ...piece,
      x: piece.x + piece.vx * seconds,
      y: piece.y + vy * seconds,
      vy,
      rotation: piece.rotation + piece.spin * seconds,
    };
    if (next.y <= height) moved.push(next);
  }
  return moved;
}
