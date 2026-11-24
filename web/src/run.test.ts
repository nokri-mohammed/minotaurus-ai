import { expect, test } from "bun:test";
import { idleRun, reduceRun } from "./run";

test("a finished run", () => {
  let s = reduceRun(idleRun, { type: "run_started", level_id: "easy-01", start: { x: 1, y: 1 }, step_limit: 52 });
  expect(s.phase).toBe("running");
  expect(s.pos).toEqual({ x: 1, y: 1 });
  expect(s.stepLimit).toBe(52);
  s = reduceRun(s, { type: "tick", n: 1, x: 1, y: 2 });
  s = reduceRun(s, { type: "tick", n: 2, x: 1, y: 3 });
  expect(s.steps).toBe(2);
  expect(s.seconds).toBeCloseTo(0.2);
  expect(s.trail).toEqual([{ x: 1, y: 1 }, { x: 1, y: 2 }]);
  s = reduceRun(s, { type: "result", status: "finished", steps: 2, seconds: 0.2 });
  expect(s.phase).toBe("done");
  expect(s.result).toEqual({ status: "finished", steps: 2, seconds: 0.2 });
});

test("timed out and error end the run", () => {
  const started = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 3 });
  expect(reduceRun(started, { type: "result", status: "timed_out", steps: 3, seconds: 0.3 }).result?.status).toBe("timed_out");
  const err = reduceRun(started, { type: "error", message: "bad" });
  expect(err.phase).toBe("done");
  expect(err.result).toEqual({ status: "error", steps: 0, seconds: 0, message: "bad" });
});

test("a new run_started resets everything", () => {
  let s = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 3 });
  s = reduceRun(s, { type: "tick", n: 1, x: 2, y: 1 });
  s = reduceRun(s, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 3 });
  expect(s.steps).toBe(0);
  expect(s.trail).toEqual([]);
});

test("reset goes back to idle", () => {
  let s = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 3 });
  s = reduceRun(s, { type: "result", status: "finished", steps: 1, seconds: 0.1 });
  expect(reduceRun(s, { type: "reset" })).toEqual(idleRun);
});

test("the trail plus the current square is the whole path: one more square than steps", () => {
  let state = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 9 });
  state = reduceRun(state, { type: "tick", n: 1, x: 2, y: 1 });
  state = reduceRun(state, { type: "tick", n: 2, x: 2, y: 2 });
  expect(state.trail.length + 1).toBe(state.steps + 1);
  expect(state.trail[0]).toEqual({ x: 1, y: 1 });
  expect(state.pos).toEqual({ x: 2, y: 2 });
});

test("stopped ends the run with the steps so far", () => {
  let s = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 9 });
  s = reduceRun(s, { type: "tick", n: 1, x: 2, y: 1 });
  s = reduceRun(s, { type: "tick", n: 2, x: 3, y: 1 });
  s = reduceRun(s, { type: "stopped" });
  expect(s.phase).toBe("done");
  expect(s.result).toEqual({ status: "stopped", steps: 2, seconds: 0.2 });
});

test("messages that arrive after a stop are ignored", () => {
  let s = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 9 });
  s = reduceRun(s, { type: "tick", n: 1, x: 2, y: 1 });
  s = reduceRun(s, { type: "stopped" });
  const after = reduceRun(s, { type: "tick", n: 2, x: 3, y: 1 });
  expect(after).toEqual(s);
  expect(reduceRun(s, { type: "result", status: "timed_out", steps: 9, seconds: 0.9 })).toEqual(s);
});

test("a stuck result ends the run and keeps its message", () => {
  const started = reduceRun(idleRun, { type: "run_started", level_id: "a", start: { x: 1, y: 1 }, step_limit: 500 });
  const s = reduceRun(started, { type: "result", status: "stuck", steps: 120, seconds: 12, message: "no new square for 100 steps" });
  expect(s.phase).toBe("done");
  expect(s.result).toEqual({ status: "stuck", steps: 120, seconds: 12, message: "no new square for 100 steps" });
});
