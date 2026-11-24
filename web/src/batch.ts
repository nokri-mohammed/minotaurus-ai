// Plain words for the result of "run all levels".
import type { BatchResult } from "./protocol";

export function batchPercent(batch: Pick<BatchResult, "total" | "finished">): number {
  if (batch.total === 0) return 0;
  return Math.round((batch.finished * 100) / batch.total);
}

/** Example: "12 of 19 finished (63%)". */
export function batchSummary(batch: Pick<BatchResult, "total" | "finished">): string {
  return `${batch.finished} of ${batch.total} finished (${batchPercent(batch)}%)`;
}

/** Finished and total for one group of levels, for example the hand-made ones. */
export function groupCount(batch: BatchResult, group: "hand-made" | "test"): { finished: number; total: number } {
  let finished = 0;
  let total = 0;
  for (const row of batch.results) {
    if (row.group !== group) continue;
    total += 1;
    if (row.status === "finished") finished += 1;
  }
  return { finished, total };
}
