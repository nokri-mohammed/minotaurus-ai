import { expect, test } from "bun:test";
import { type Attempt, addAttempt, loadAttempts } from "./history";

function memory() {
  const data = new Map<string, string>();
  return {
    getItem: (k: string) => data.get(k) ?? null,
    setItem: (k: string, v: string) => void data.set(k, v),
  };
}

const sample = (id: string, extra: Partial<Attempt> = {}): Attempt => ({
  id, date: "2026-11-21T10:00:00Z", brain: "q1.onnx", method: "qtable", level: "easy-01",
  result: "finished", steps: 13, seconds: 1.3, ...extra,
});

test("starts empty", () => {
  expect(loadAttempts(memory())).toEqual([]);
});

test("adds attempts newest first and keeps them", () => {
  const store = memory();
  addAttempt(sample("a"), store);
  const list = addAttempt(sample("b", { result: "timed_out" }), store);
  expect(list.map((a) => a.id)).toEqual(["b", "a"]);
  expect(loadAttempts(store).map((a) => a.id)).toEqual(["b", "a"]);
});

test("survives broken storage", () => {
  const broken = {
    getItem: () => { throw new Error("blocked"); },
    setItem: () => { throw new Error("blocked"); },
  };
  expect(loadAttempts(broken)).toEqual([]);
  expect(addAttempt(sample("a"), broken).map((a) => a.id)).toEqual(["a"]);
  expect(loadAttempts(undefined)).toEqual([]);
});

test("ignores corrupt or invalid saved data", () => {
  const store = memory();
  store.setItem("minotaurus.attempts.v1", "{oops");
  expect(loadAttempts(store)).toEqual([]);
  store.setItem("minotaurus.attempts.v1", JSON.stringify([sample("ok"), { id: 5 }, null]));
  expect(loadAttempts(store).map((a) => a.id)).toEqual(["ok"]);
});

import { summarize } from "./history";

test("summary counts attempts, finishes and the best time", () => {
  expect(summarize([])).toEqual({ total: 0, finished: 0, bestSeconds: null });
  const list = [
    sample("a", { seconds: 1.3 }),
    sample("b", { result: "timed_out", seconds: 5.2 }),
    sample("c", { seconds: 0.9 }),
  ];
  expect(summarize(list)).toEqual({ total: 3, finished: 2, bestSeconds: 0.9 });
});

test("an attempt keeps its path when saved", () => {
  const store = memory();
  addAttempt(sample("a", { path: [[1, 1], [2, 1]] }), store);
  expect(loadAttempts(store)[0].path).toEqual([[1, 1], [2, 1]]);
});

test("only the newest 30 attempts keep their path", () => {
  const store = memory();
  let list: Attempt[] = [];
  for (let i = 0; i < 32; i++) list = addAttempt(sample(`a${i}`, { path: [[1, 1]] }), store);
  expect(list.length).toBe(32);
  expect(list[0].path).toBeDefined();
  expect(list[29].path).toBeDefined();
  expect(list[30].path).toBeUndefined();
  expect(list[31].path).toBeUndefined();
});

test("an attempt with a broken path is ignored", () => {
  const store = memory();
  store.setItem("minotaurus.attempts.v1", JSON.stringify([{ ...sample("a"), path: "nope" }, sample("b")]));
  expect(loadAttempts(store).map((a) => a.id)).toEqual(["b"]);
});
