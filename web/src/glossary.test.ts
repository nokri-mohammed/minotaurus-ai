import { expect, test } from "bun:test";
import { glossaryLabels, tipFor } from "./glossary";
import { recipeSections } from "./recipe";
import type { BrainRecipe } from "./protocol";

test("every tip is short, and has no em dash", () => {
  for (const label of glossaryLabels()) {
    const text = tipFor(label) ?? "";
    expect(text.length).toBeGreaterThan(5);
    expect(text.length).toBeLessThanOrEqual(90);
    expect(text.includes("—")).toBe(false);
  }
});

test("a label that is not explained has no tip", () => {
  expect(tipFor("Nope")).toBeNull();
});

test("every label of a full recipe has a tip", () => {
  const recipe = {
    config: {
      method: "dqn", seed: 1, wall_mask: true, loop_escape: true, observation: { window: 5, version: 2 },
      loop_stop: { repeats: 3, penalty: 0.5 }, episodes: 100, eval_every: 10, patience: 5,
      levels: { generated: { sizes: [9, 11], train: 1, validation: 1, test: 1, maze_seed: 3, border_exit: true } },
      dqn: {
        hidden_layers: [64, 64], learning_rate: 0.001, batch_size: 32, gamma: 0.9, replay_size: 1000, target_update: 100,
        epsilon_start: 1, epsilon_end: 0.1, epsilon_decay: 0.99, shaping: true, novelty_bonus: 0.1, revisit_penalty: 0.1,
        imitation: { episodes: 10, teacher_share: 0.5, margin: 0.8, weight: 1 },
      },
    },
    scores: { train: 1, validation: 0.5, test: 0.5 },
    fixed_levels: { a: true },
    test_stats: { avg_steps: 10, avg_path_ratio: 1.2 },
    has_graph: false,
  } as unknown as BrainRecipe;
  const missing: string[] = [];
  for (const section of recipeSections(recipe)) {
    for (const row of section.rows) {
      if (tipFor(row.label) === null) missing.push(row.label);
    }
  }
  expect(missing).toEqual([]);
});
