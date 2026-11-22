// Chart helpers: pure functions that turn saved attempts into numbers and points for the SVG.
import type { Attempt } from "./services/history";

export type Outcomes = { finished: number; timed_out: number; error: number };
export type Box = { width: number; height: number; pad: number };
export type XY = { x: number; y: number };

/** Steps of the finished attempts, oldest first. (Attempts are saved newest first.) */
export function stepsOverTime(attempts: Attempt[]): number[] {
  const steps: number[] = [];
  for (let i = attempts.length - 1; i >= 0; i -= 1) {
    if (attempts[i].result === "finished") steps.push(attempts[i].steps);
  }
  return steps;
}

export function countOutcomes(attempts: Attempt[]): Outcomes {
  const counts: Outcomes = { finished: 0, timed_out: 0, error: 0 };
  for (const attempt of attempts) {
    counts[attempt.result] += 1;
  }
  return counts;
}

/**
 * Where to draw each value in a box. x is spread evenly (one value sits in the middle).
 * y starts at zero at the bottom, so the line never exaggerates a small change.
 */
export function layoutLine(values: number[], box: Box): XY[] {
  if (values.length === 0) return [];
  let max = 0;
  for (const value of values) {
    if (value > max) max = value;
  }
  const innerWidth = box.width - 2 * box.pad;
  const innerHeight = box.height - 2 * box.pad;
  const points: XY[] = [];
  for (let i = 0; i < values.length; i += 1) {
    const x = values.length === 1 ? box.width / 2 : box.pad + (innerWidth * i) / (values.length - 1);
    const share = max === 0 ? 0 : values[i] / max;
    const y = box.pad + innerHeight * (1 - share);
    points.push({ x, y });
  }
  return points;
}
