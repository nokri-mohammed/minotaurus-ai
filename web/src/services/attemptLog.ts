// The downloadable log of one attempt: every square the brain stood on, with the game time.
import type { Attempt } from "./history";

export const STEP_SECONDS = 0.1; // game time of one step (the same as the page's run clock)

export type Move = "up" | "down" | "left" | "right" | "blocked";

export type LogStep = { n: number; x: number; y: number; seconds: number; move: Move | null };

export type AttemptLog = {
  format: "minotaurus-attempt-log";
  version: 1;
  step_seconds: number;
  attempt: Pick<Attempt, "id" | "date" | "brain" | "method" | "level" | "result" | "steps" | "seconds">;
  steps: LogStep[];
};

// The move that took the brain from one square to the next. The same square means it walked
// into a wall. y grows downwards, so up is a smaller y.
function moveBetween(from: [number, number], to: [number, number]): Move {
  if (to[0] > from[0]) return "right";
  if (to[0] < from[0]) return "left";
  if (to[1] > from[1]) return "down";
  if (to[1] < from[1]) return "up";
  return "blocked";
}

export function buildAttemptLog(attempt: Attempt): AttemptLog {
  const steps: LogStep[] = [];
  const path = attempt.path ?? [];
  for (let n = 0; n < path.length; n++) {
    const [x, y] = path[n];
    steps.push({
      n,
      x,
      y,
      seconds: Math.round(n * STEP_SECONDS * 10) / 10,
      move: n === 0 ? null : moveBetween(path[n - 1], path[n]),
    });
  }
  return {
    format: "minotaurus-attempt-log",
    version: 1,
    step_seconds: STEP_SECONDS,
    attempt: {
      id: attempt.id, date: attempt.date, brain: attempt.brain, method: attempt.method,
      level: attempt.level, result: attempt.result, steps: attempt.steps, seconds: attempt.seconds,
    },
    steps,
  };
}

/** Example: minotaurus-easy-01-2026-11-24-abcdef12.json */
export function logFileName(attempt: Attempt): string {
  return `minotaurus-${attempt.level}-${attempt.date.slice(0, 10)}-${attempt.id.slice(0, 8)}.json`;
}

/** Ask the browser to save the log as a file. */
export function downloadAttemptLog(attempt: Attempt): void {
  const text = JSON.stringify(buildAttemptLog(attempt), null, 2);
  const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = logFileName(attempt);
  link.click();
  URL.revokeObjectURL(url);
}
