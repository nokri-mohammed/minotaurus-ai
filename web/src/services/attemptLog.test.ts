import { expect, test } from "bun:test";
import { allLogsFileName, buildAllLogs, buildAttemptLog, logFileName } from "./attemptLog";
import type { Attempt } from "./history";

const attempt: Attempt = {
  id: "abcdef12-0000", date: "2026-11-24T10:00:00Z", brain: "q1.onnx", method: "qtable",
  level: "easy-01", result: "finished", steps: 4, seconds: 0.4,
  path: [[1, 1], [2, 1], [2, 1], [2, 2], [1, 2]],
};

test("the log has one entry per position, starting at step 0", () => {
  const log = buildAttemptLog(attempt);
  expect(log.steps.length).toBe(5);
  expect(log.steps[0]).toEqual({ n: 0, x: 1, y: 1, seconds: 0, move: null });
});

test("each step has its game time and the move that led to it", () => {
  const log = buildAttemptLog(attempt);
  expect(log.steps[1]).toEqual({ n: 1, x: 2, y: 1, seconds: 0.1, move: "right" });
  expect(log.steps[2].move).toBe("blocked"); // same square: it walked into a wall
  expect(log.steps[3].move).toBe("down");
  expect(log.steps[4]).toEqual({ n: 4, x: 1, y: 2, seconds: 0.4, move: "left" });
});

test("up is a smaller y", () => {
  const log = buildAttemptLog({ ...attempt, path: [[1, 2], [1, 1]] });
  expect(log.steps[1].move).toBe("up");
});

test("the log names the attempt, its result and the step length", () => {
  const log = buildAttemptLog(attempt);
  expect(log.format).toBe("minotaurus-attempt-log");
  expect(log.version).toBe(1);
  expect(log.step_seconds).toBe(0.1);
  expect(log.attempt).toEqual({
    id: "abcdef12-0000", date: "2026-11-24T10:00:00Z", brain: "q1.onnx", method: "qtable",
    level: "easy-01", result: "finished", steps: 4, seconds: 0.4,
  });
});

test("an attempt saved without a path gives an empty step list", () => {
  const { path: _path, ...old } = attempt;
  expect(buildAttemptLog(old).steps).toEqual([]);
});

test("the file name has the level, the day and the start of the id", () => {
  expect(logFileName(attempt)).toBe("minotaurus-easy-01-2026-11-24-abcdef12.json");
});

test("all logs in one file: only the attempts that have a path", () => {
  const without: Attempt = { ...attempt, id: "no-path-00", path: undefined };
  const all = buildAllLogs([attempt, without], new Date("2026-11-24T12:00:00Z"));
  expect(all.format).toBe("minotaurus-attempt-logs");
  expect(all.version).toBe(1);
  expect(all.exported).toBe("2026-11-24T12:00:00.000Z");
  expect(all.count).toBe(1);
  expect(all.logs.length).toBe(1);
  expect(all.logs[0].attempt.id).toBe("abcdef12-0000");
  expect(all.logs[0].steps.length).toBe(5);
});

test("the file name of all logs has the day", () => {
  expect(allLogsFileName(new Date("2026-11-24T12:00:00Z"))).toBe("minotaurus-all-logs-2026-11-24.json");
});
