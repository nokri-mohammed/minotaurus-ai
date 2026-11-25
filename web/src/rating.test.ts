import { expect, test } from "bun:test";
import { ratingOf, starsFor } from "./rating";
import type { BatchResult } from "./protocol";

type Row = BatchResult["results"][number];
const row = (id: string, group: Row["group"], status: Row["status"], steps: number, seconds: number): Row =>
  ({ level_id: id, name: id, group, status, steps, seconds });

const batch = (results: Row[]): BatchResult => {
  let finished = 0;
  for (const r of results) if (r.status === "finished") finished += 1;
  return { id: "b", brain_id: "a".repeat(64), date: "2026-11-25T10:00:00+00:00", total: results.length, finished, results };
};

test("stars follow the share of levels finished, from 0 to 5", () => {
  expect(starsFor(0, 19)).toBe(0);
  expect(starsFor(19, 19)).toBe(5);
  expect(starsFor(10, 20)).toBe(3); // half rounds up
  expect(starsFor(12, 19)).toBe(3); // 63%
  expect(starsFor(1, 19)).toBe(0); // under 10% is not a star yet
  expect(starsFor(0, 0)).toBe(0);
});

test("the rating counts what finished, and steps and time only of finished levels", () => {
  const rating = ratingOf(
    batch([
      row("easy-01", "hand-made", "finished", 13, 1.3),
      row("hard-01", "hand-made", "timed_out", 500, 50),
      row("t1", "test", "finished", 30, 3),
      row("t2", "test", "stuck", 90, 9),
      row("t3", "test", "error", 0, 0),
    ]),
  );
  expect(rating.finished).toBe(2);
  expect(rating.total).toBe(5);
  expect(rating.percent).toBe(40);
  expect(rating.stars).toBe(2);
  expect(rating.steps).toBe(43);
  expect(rating.seconds).toBeCloseTo(4.3);
  expect(rating.handMade).toEqual({ finished: 1, total: 2 });
  expect(rating.test).toEqual({ finished: 1, total: 3 });
  expect(rating.timedOut).toBe(1);
  expect(rating.stuck).toBe(1);
  expect(rating.errors).toBe(1);
  expect(rating.averageSteps).toBe(21.5);
});

test("no finished level means no average", () => {
  expect(ratingOf(batch([row("a", "test", "timed_out", 9, 1)])).averageSteps).toBeNull();
});
