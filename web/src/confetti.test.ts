import { describe, expect, test } from "bun:test";
import { CONFETTI_COLORS, makePieces, stepPieces } from "./confetti";

// A fixed "random" so the tests give the same result every time.
function sequence(values: number[]): () => number {
  let i = 0;
  return () => {
    const value = values[i % values.length];
    i += 1;
    return value;
  };
}

describe("makePieces", () => {
  test("makes the asked number of pieces, spread across the width, above the top edge", () => {
    const pieces = makePieces(40, 800, sequence([0.1, 0.5, 0.9, 0.3]));
    expect(pieces.length).toBe(40);
    for (const piece of pieces) {
      expect(piece.x).toBeGreaterThanOrEqual(0);
      expect(piece.x).toBeLessThanOrEqual(800);
      expect(piece.y).toBeLessThanOrEqual(0);
      expect(CONFETTI_COLORS).toContain(piece.color);
    }
  });

  test("makes nothing for a count of 0", () => {
    expect(makePieces(0, 800).length).toBe(0);
  });
});

describe("stepPieces", () => {
  test("pieces fall: y grows and the fall speeds up", () => {
    const [piece] = makePieces(1, 800, sequence([0.5]));
    const [moved] = stepPieces([piece], 0.1, 600);
    expect(moved.y).toBeGreaterThan(piece.y);
    expect(moved.vy).toBeGreaterThan(piece.vy);
  });

  test("pieces that fall below the bottom edge are dropped", () => {
    const [piece] = makePieces(1, 800, sequence([0.5]));
    const below = { ...piece, y: 700 };
    expect(stepPieces([below], 0.1, 600).length).toBe(0);
  });

  test("the input list is not changed", () => {
    const pieces = makePieces(3, 800, sequence([0.2, 0.7]));
    const before = pieces[0].y;
    stepPieces(pieces, 0.5, 600);
    expect(pieces[0].y).toBe(before);
  });
});
