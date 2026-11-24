import { expect, test } from "bun:test";
import { brainRow, compareRecipes, pileKey, pileLabel, trendPoints } from "./brainsView";
import type { BatchResult, BrainInfo, BrainRecipe } from "./protocol";

const config = (extra: Record<string, unknown> = {}, sizes = [9, 11, 13]) => ({
  name: "d", method: "dqn", seed: 1, episodes: 15000,
  levels: { generated: { size: 9, sizes, maze_seed: 1, train: 600, validation: 120, test: 120, border_exit: true } },
  dqn: { hidden_layers: [128, 128], learning_rate: 0.001, target_update: 200, epsilon_start: 1, epsilon_end: 0.05, epsilon_decay: 0.997, ...extra },
});

const recipe = (cfg: Record<string, unknown>, exam = 0.8, fixed = { "easy-01": true, "hard-01": false }): BrainRecipe => ({
  bundle_version: 1, has_graph: true, config: cfg,
  scores: { train: 0.9, validation: exam + 0.01, test: exam },
  fixed_levels: fixed, test_stats: { avg_steps: 100, avg_path_ratio: 1.1 },
});

const brain = (id: string, name: string, added = "2026-11-24T10:00:00+00:00"): BrainInfo => ({
  id: id.repeat(64).slice(0, 64), name, method: "dqn", has_recipe: true, added_at: added,
});

test("the exam pile is named from the mazes, so only equal piles are compared", () => {
  expect(pileKey(recipe(config()))).toBe(pileKey(recipe(config({ learning_rate: 0.0003 }))));
  expect(pileKey(recipe(config()))).not.toBe(pileKey(recipe(config({}, [9, 11, 13, 17, 21]))));
  expect(pileLabel(recipe(config()))).toBe("sizes 9, 11, 13 / 120 exam");
  expect(pileKey({ bundle_version: 1, has_graph: false, config: { levels: ["easy-01"] } })).toBeNull();
});

test("a row has the numbers the table shows", () => {
  const batch = { total: 19, finished: 12 } as BatchResult;
  const row = brainRow(brain("a", "one"), recipe(config()), batch);
  expect(row.exam).toBe(0.8);
  expect(row.quiz).toBeCloseTo(0.81);
  expect(row.portal).toBe("1 of 2");
  expect(row.runAll).toBe("12 of 19 (63%)");
  expect(row.network).toBe("128 × 128");
  expect(row.learningRate).toBe("0.001");
  const bare = brainRow({ ...brain("b", "plain"), has_recipe: false }, null, null);
  expect(bare.exam).toBeNull();
  expect(bare.runAll).toBe("–");
});

test("compare shows only the settings that differ, and the results apart", () => {
  const a = recipe(config(), 0.7);
  const b = recipe(config({ learning_rate: 0.0003, target_update: 1000 }), 0.8);
  const result = compareRecipes(a, b);
  const labels = result.settings.map((r) => r.label);
  expect(labels).toEqual(["Learning: Learning rate", "Learning: Target update"]);
  expect(result.settings[0]).toEqual({ label: "Learning: Learning rate", a: "0.001", b: "0.0003" });
  expect(result.results.map((r) => r.label)).toContain("Result: Exam (test)");
  expect(result.samePile).toBe(true);
});

test("compare says when the exam piles differ", () => {
  const result = compareRecipes(recipe(config()), recipe(config({}, [9, 11, 13, 17, 21])));
  expect(result.samePile).toBe(false);
});

test("the trend lists exam scores of one pile, oldest first", () => {
  const first = brain("a", "one", "2026-11-24T10:00:00+00:00");
  const second = brain("b", "two", "2026-11-24T12:00:00+00:00");
  const other = brain("c", "wide", "2026-11-24T11:00:00+00:00");
  const key = pileKey(recipe(config())) as string;
  const points = trendPoints(
    [
      { brain: second, recipe: recipe(config(), 0.9) },
      { brain: first, recipe: recipe(config(), 0.7) },
      { brain: other, recipe: recipe(config({}, [9, 21]), 0.5) },
      { brain: brain("d", "plain"), recipe: null },
    ],
    key,
  );
  expect(points.map((p) => p.name)).toEqual(["one", "two"]);
  expect(points.map((p) => p.exam)).toEqual([0.7, 0.9]);
});
