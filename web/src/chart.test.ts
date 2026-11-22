import { describe, expect, test } from "bun:test";
import { countOutcomes, layoutLine, stepsOverTime } from "./chart";
import type { Attempt } from "./services/history";

function attempt(id: string, result: Attempt["result"], steps: number): Attempt {
  return { id, date: "2026-11-22T10:00:00.000Z", brain: "b", method: "qtable", level: "easy-01", result, steps, seconds: steps / 10 };
}

// The page keeps attempts newest first.
const NEWEST_FIRST = [
  attempt("c", "finished", 13),
  attempt("b", "timed_out", 52),
  attempt("a", "finished", 30),
];

describe("stepsOverTime", () => {
  test("gives the finished attempts, oldest first, as step counts", () => {
    expect(stepsOverTime(NEWEST_FIRST)).toEqual([30, 13]);
  });
  test("is empty when nothing finished", () => {
    expect(stepsOverTime([attempt("x", "error", 3)])).toEqual([]);
  });
});

describe("countOutcomes", () => {
  test("counts finished, timed out and failed runs", () => {
    expect(countOutcomes([...NEWEST_FIRST, attempt("d", "error", 2)])).toEqual({ finished: 2, timed_out: 1, error: 1 });
  });
  test("is all zeros for no attempts", () => {
    expect(countOutcomes([])).toEqual({ finished: 0, timed_out: 0, error: 0 });
  });
});

describe("layoutLine", () => {
  const box = { width: 300, height: 100, pad: 10 };

  test("spreads points across the width and starts the scale at zero", () => {
    const points = layoutLine([30, 15], box);
    expect(points.length).toBe(2);
    expect(points[0].x).toBe(10);
    expect(points[1].x).toBe(290);
    // 30 is the max, so it sits at the top; 15 is half way down to the zero line.
    expect(points[0].y).toBe(10);
    expect(points[1].y).toBe(50);
  });

  test("a single value sits in the middle", () => {
    const points = layoutLine([13], box);
    expect(points[0].x).toBe(150);
  });

  test("no values gives no points", () => {
    expect(layoutLine([], box)).toEqual([]);
  });
});
