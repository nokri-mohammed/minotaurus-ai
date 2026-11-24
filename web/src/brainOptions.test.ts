import { expect, test } from "bun:test";
import { brainLabel, brainOptions, shortId, withBrain } from "./brainOptions";
import type { BrainInfo } from "./protocol";

const make = (id: string, name: string): BrainInfo => ({
  id: id.repeat(64).slice(0, 64), name, method: "dqn", has_recipe: true, added_at: "2026-11-24T10:00:00+00:00",
});

test("a brain is named with its short id", () => {
  const brain = make("a3f9c21e", "wide");
  expect(shortId(brain.id)).toBe("a3f9c21e");
  expect(brainLabel(brain)).toBe("wide (a3f9c21e)");
});

test("options keep the order of the brains", () => {
  const options = brainOptions([make("a", "one"), make("b", "two")]);
  expect(options.map((o) => o.label)).toEqual(["one (aaaaaaaa)", "two (bbbbbbbb)"]);
});

test("a loaded brain goes to the top and is never listed twice", () => {
  const list = withBrain([make("a", "one"), make("b", "two")], make("b", "two"));
  expect(list.map((b) => b.name)).toEqual(["two", "one"]);
  expect(withBrain([], make("c", "new")).length).toBe(1);
});
