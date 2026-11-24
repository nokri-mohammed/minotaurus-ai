import { expect, test } from "bun:test";
import type { Attempt } from "../history";
import { fromRecord, toRecord } from "./attempts";

const attempt: Attempt = {
  id: "a1", date: "2026-11-24T10:00:00Z", brainId: "c".repeat(64), brain: "d1", method: "dqn",
  level: "easy-01", result: "finished", steps: 13, seconds: 1.3, path: [[1, 1], [1, 2]],
};

test("an attempt becomes a server record and back", () => {
  const record = toRecord(attempt);
  expect(record.brain_id).toBe("c".repeat(64));
  expect(record.path).toEqual([[1, 1], [1, 2]]);
  expect(fromRecord(record)).toEqual(attempt);
});

test("a record without a path comes back without one", () => {
  const { path: _p, ...rest } = attempt;
  const back = fromRecord({ ...toRecord(attempt), path: null });
  expect(back).toEqual(rest);
  expect("path" in back).toBe(false);
});
