// The rating of a brain, worked out from its latest "run all levels" result.
import { batchPercent, groupCount } from "./batch";
import type { BatchResult } from "./protocol";

export const MAX_STARS = 5;

export type Rating = {
  stars: number; // 0 to 5
  finished: number;
  total: number;
  percent: number;
  steps: number; // steps of the levels it finished
  seconds: number; // game time of the levels it finished
  averageSteps: number | null; // per finished level
  handMade: { finished: number; total: number };
  test: { finished: number; total: number };
  timedOut: number;
  stuck: number;
  errors: number;
};

/** Whole stars out of five for the share of levels finished (half a star rounds up). */
export function starsFor(finished: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((finished * MAX_STARS) / total);
}

export function ratingOf(batch: BatchResult): Rating {
  let steps = 0;
  let seconds = 0;
  let timedOut = 0;
  let stuck = 0;
  let errors = 0;
  for (const row of batch.results) {
    if (row.status === "finished") {
      steps += row.steps;
      seconds += row.seconds;
    }
    if (row.status === "timed_out") timedOut += 1;
    if (row.status === "stuck") stuck += 1;
    if (row.status === "error") errors += 1;
  }
  let averageSteps: number | null = null;
  if (batch.finished > 0) averageSteps = steps / batch.finished;
  return {
    stars: starsFor(batch.finished, batch.total),
    finished: batch.finished,
    total: batch.total,
    percent: batchPercent(batch),
    steps,
    seconds,
    averageSteps,
    handMade: groupCount(batch, "hand-made"),
    test: groupCount(batch, "test"),
    timedOut,
    stuck,
    errors,
  };
}
