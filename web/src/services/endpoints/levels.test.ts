import { expect, test } from "bun:test";
import type { LevelInfo } from "../../protocol";
import { ApiService } from "../ApiService";
import { getLevels } from "./levels";

const LEVEL: LevelInfo = { id: "easy-01", name: "First steps", difficulty: "easy", grid: ["#S.E#"], step_limit: 8 };
const serving = (body: unknown) => new ApiService({ fetchFn: (async () => new Response(JSON.stringify(body))) as unknown as typeof fetch });

test("getLevels returns the validated list", async () => {
  expect(await getLevels(serving([LEVEL]))).toEqual([LEVEL]);
});

test("getLevels rejects a level that breaks the contract", async () => {
  await expect(getLevels(serving([{ ...LEVEL, difficulty: "insane" }]))).rejects.toThrow("unexpected reply");
});
