import { expect, test } from "bun:test";
import samples from "../../data/schemas/message-samples.json";
import { brainInfoSchema, levelsSchema, parseRunMessage, runMessageSchema } from "./protocol";

test("every shared valid sample parses, every invalid one is rejected", () => {
  for (const s of samples.run_message.valid) expect(runMessageSchema.safeParse(s).success).toBe(true);
  for (const s of samples.run_message.invalid) expect(runMessageSchema.safeParse(s).success).toBe(false);
  for (const s of samples.levels_response.valid) expect(levelsSchema.safeParse(s).success).toBe(true);
  for (const s of samples.levels_response.invalid) expect(levelsSchema.safeParse(s).success).toBe(false);
  for (const s of samples.brain_response.valid) expect(brainInfoSchema.safeParse(s).success).toBe(true);
  for (const s of samples.brain_response.invalid) expect(brainInfoSchema.safeParse(s).success).toBe(false);
});

test("parseRunMessage reads a text frame", () => {
  expect(parseRunMessage('{"type":"tick","n":3,"x":1,"y":3}')).toEqual({ type: "tick", n: 3, x: 1, y: 3 });
  expect(parseRunMessage('{"type":"result","status":"finished","steps":13,"seconds":1.3}')?.type).toBe("result");
});

test("parseRunMessage returns null for garbage", () => {
  expect(parseRunMessage("not json")).toBeNull();
  expect(parseRunMessage("[]")).toBeNull();
  expect(parseRunMessage('{"type":"nope"}')).toBeNull();
});
