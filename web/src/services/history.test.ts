import { expect, test } from "bun:test";
import {
  type Attempt, attemptsOf, loadLocalAttempts, markMigrated, migrationDone, recentAttempts, summarize,
} from "./history";

function memory() {
  const data = new Map<string, string>();
  return {
    getItem: (k: string) => data.get(k) ?? null,
    setItem: (k: string, v: string) => void data.set(k, v),
  };
}

const sample = (id: string, extra: Partial<Attempt> = {}): Attempt => ({
  id, date: "2026-11-21T10:00:00Z", brainId: "a".repeat(64), brain: "q1.onnx", method: "qtable", level: "easy-01",
  result: "finished", steps: 13, seconds: 1.3, ...extra,
});

test("no saved browser attempts gives an empty list", () => {
  expect(loadLocalAttempts(memory())).toEqual([]);
});

test("older browser attempts get the brain id unknown", () => {
  const store = memory();
  const { brainId: _b, ...old } = sample("a");
  store.setItem("minotaurus.attempts.v1", JSON.stringify([old]));
  expect(loadLocalAttempts(store)[0].brainId).toBe("unknown");
});

test("broken storage and corrupt data never throw", () => {
  const broken = {
    getItem: () => { throw new Error("blocked"); },
    setItem: () => { throw new Error("blocked"); },
  };
  expect(loadLocalAttempts(broken)).toEqual([]);
  expect(loadLocalAttempts(undefined)).toEqual([]);
  expect(migrationDone(broken)).toBe(false);
  expect(() => markMigrated(broken)).not.toThrow();
  const store = memory();
  store.setItem("minotaurus.attempts.v1", "{oops");
  expect(loadLocalAttempts(store)).toEqual([]);
  store.setItem("minotaurus.attempts.v1", JSON.stringify([sample("ok"), { id: 5 }, null]));
  expect(loadLocalAttempts(store).map((a) => a.id)).toEqual(["ok"]);
});

test("the migration flag is remembered", () => {
  const store = memory();
  expect(migrationDone(store)).toBe(false);
  markMigrated(store);
  expect(migrationDone(store)).toBe(true);
});

test("summary counts attempts, finishes and the best time", () => {
  expect(summarize([])).toEqual({ total: 0, finished: 0, bestSeconds: null });
  const list = [
    sample("a", { seconds: 1.3 }),
    sample("b", { result: "timed_out", seconds: 5.2 }),
    sample("c", { seconds: 0.9 }),
  ];
  expect(summarize(list)).toEqual({ total: 3, finished: 2, bestSeconds: 0.9 });
});

test("recentAttempts keeps the newest few", () => {
  const list = [sample("a"), sample("b"), sample("c")];
  expect(recentAttempts(list, 2).map((a) => a.id)).toEqual(["a", "b"]);
});

test("attemptsOf keeps only one brain's attempts, in order", () => {
  const other = "b".repeat(64);
  const list = [sample("a"), sample("b", { brainId: other }), sample("c")];
  expect(attemptsOf(list, "a".repeat(64)).map((a) => a.id)).toEqual(["a", "c"]);
  expect(attemptsOf(list, null)).toEqual([]);
});
