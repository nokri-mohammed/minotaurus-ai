import { expect, test } from "bun:test";
import { parseRunMessage } from "./protocol";

test("parses the four run messages", () => {
  expect(parseRunMessage('{"type":"run_started","level_id":"easy-01","start":{"x":1,"y":1},"step_limit":52}')).toEqual({
    type: "run_started", level_id: "easy-01", start: { x: 1, y: 1 }, step_limit: 52,
  });
  expect(parseRunMessage('{"type":"tick","n":3,"x":1,"y":3}')).toEqual({ type: "tick", n: 3, x: 1, y: 3 });
  expect(parseRunMessage('{"type":"result","status":"finished","steps":13,"seconds":1.3}')?.type).toBe("result");
  expect(parseRunMessage('{"type":"error","message":"bad brain"}')).toEqual({ type: "error", message: "bad brain" });
});

test("rejects unknown, malformed and incomplete messages", () => {
  expect(parseRunMessage("not json")).toBeNull();
  expect(parseRunMessage('{"type":"nope"}')).toBeNull();
  expect(parseRunMessage('{"type":"tick","n":"3","x":1,"y":3}')).toBeNull();
  expect(parseRunMessage('{"type":"tick","n":3}')).toBeNull();
  expect(parseRunMessage('{"type":"result","status":"won","steps":1,"seconds":1}')).toBeNull();
  expect(parseRunMessage("[]")).toBeNull();
});
