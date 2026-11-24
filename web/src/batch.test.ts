import { expect, test } from "bun:test";
import { batchPercent, batchSummary, groupCount } from "./batch";
import type { BatchResult } from "./protocol";

const row = (level_id: string, group: "hand-made" | "test", status: "finished" | "timed_out") =>
  ({ level_id, name: level_id, group, status, steps: 10, seconds: 1 }) as const;

const batch: BatchResult = {
  id: "b1", brain_id: "a".repeat(64), date: "2026-11-24T10:00:00+00:00", total: 3, finished: 2,
  results: [row("easy-01", "hand-made", "finished"), row("hard-01", "hand-made", "timed_out"), row("test-09-01", "test", "finished")],
};

test("the summary says how many finished and the percent", () => {
  expect(batchSummary(batch)).toBe("2 of 3 finished (67%)");
  expect(batchPercent({ total: 0, finished: 0 })).toBe(0);
  expect(batchSummary({ total: 19, finished: 12 })).toBe("12 of 19 finished (63%)");
});

test("each group is counted on its own", () => {
  expect(groupCount(batch, "hand-made")).toEqual({ finished: 1, total: 2 });
  expect(groupCount(batch, "test")).toEqual({ finished: 1, total: 1 });
});
