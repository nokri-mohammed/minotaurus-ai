import { afterEach, expect, test } from "bun:test";
import type { LevelInfo } from "../../protocol";
import { getLevels } from "./levels";

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });
const serving = (body: unknown, status = 200) => {
  globalThis.fetch = (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;
};

const LEVEL: LevelInfo = { id: "easy-01", name: "First steps", difficulty: "easy", grid: ["#S.E#"], step_limit: 8 };

test("getLevels returns the validated list", async () => {
  serving([LEVEL]);
  expect(await getLevels()).toEqual([LEVEL]);
});

test("getLevels rejects a level that breaks the contract", async () => {
  serving([{ ...LEVEL, difficulty: "insane" }]);
  await expect(getLevels()).rejects.toThrow("unexpected reply");
});
