import { expect, test } from "bun:test";
import { atLeast } from "./minimumTime";

test("a fast result is held back until the time is up", async () => {
  const started = Date.now();
  const value = await atLeast(Promise.resolve("ok"), 60);
  expect(value).toBe("ok");
  expect(Date.now() - started).toBeGreaterThanOrEqual(55);
});

test("a failure is also held back, then thrown", async () => {
  const started = Date.now();
  await expect(atLeast(Promise.reject(new Error("refused")), 60)).rejects.toThrow("refused");
  expect(Date.now() - started).toBeGreaterThanOrEqual(55);
});

test("a slow result is not delayed any more", async () => {
  const slow = new Promise<string>((resolve) => setTimeout(() => resolve("late"), 80));
  const started = Date.now();
  expect(await atLeast(slow, 20)).toBe("late");
  expect(Date.now() - started).toBeLessThan(140);
});
