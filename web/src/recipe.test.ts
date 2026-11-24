import { expect, test } from "bun:test";
import type { BrainRecipe } from "./protocol";
import { recipeSections } from "./recipe";

const wide: BrainRecipe = {
  bundle_version: 1,
  has_graph: true,
  config: {
    name: "dqn-mixed-wide-learning", method: "dqn", seed: 4, episodes: 15000, eval_every: 250, patience: 8,
    wall_mask: true,
    levels: { generated: { size: 9, sizes: [9, 11, 13, 17, 21], maze_seed: 1, train: 750, validation: 150, test: 150, border_exit: true } },
    dqn: {
      hidden_layers: [128, 128], learning_rate: 0.001, batch_size: 64, gamma: 0.98, replay_size: 50000,
      target_update: 200, epsilon_start: 1.0, epsilon_end: 0.05, epsilon_decay: 0.997,
      shaping: true, novelty_bonus: 0.02, revisit_penalty: 0.01,
    },
  },
  scores: { train: 0.7, validation: 0.71, test: 0.69 },
  fixed_levels: { "easy-01": true, "hard-02": true, "impossible-01": false },
  test_stats: { avg_steps: 149.1, avg_path_ratio: 1.11 },
};

const find = (sections: ReturnType<typeof recipeSections>, title: string, label: string) =>
  sections.find((s) => s.title === title)?.rows.find((r) => r.label === label)?.value;

test("the mazes are described in plain words", () => {
  const sections = recipeSections(wide);
  expect(find(sections, "Mazes", "Sizes")).toBe("9, 11, 13, 17, 21");
  expect(find(sections, "Mazes", "Piles")).toBe("750 practice, 150 quiz, 150 exam");
  expect(find(sections, "Mazes", "Maze seed")).toBe("1");
});

test("the brain and its learning settings are shown", () => {
  const sections = recipeSections(wide);
  expect(find(sections, "Brain", "Method")).toBe("DQN");
  expect(find(sections, "Brain", "Network")).toBe("128 × 128");
  expect(find(sections, "Learning", "Learning rate")).toBe("0.001");
  expect(find(sections, "Learning", "Target update")).toBe("every 200 steps");
  expect(find(sections, "Exploring", "Random moves")).toBe("100% down to 5%, 0.3% less per try");
  expect(find(sections, "Rewards", "Revisit penalty")).toBe("0.01");
});

test("the result line says how the brain scored", () => {
  const sections = recipeSections(wide);
  expect(find(sections, "Result", "Quiz (validation)")).toBe("71%");
  expect(find(sections, "Result", "Exam (test)")).toBe("69%");
  expect(find(sections, "Result", "Portal levels")).toBe("2 of 3 finished");
  expect(find(sections, "Result", "Route length")).toBe("1.11 times the shortest");
});

test("a q-table recipe shows its own learning settings and no network", () => {
  const sections = recipeSections({
    bundle_version: 1, has_graph: false,
    config: { name: "q", method: "qtable", levels: ["easy-01"], episodes: 3000, seed: 1,
      qtable: { learning_rate: 0.3, gamma: 0.98, epsilon_start: 1, epsilon_end: 0.05, epsilon_decay: 0.997 } },
  });
  expect(find(sections, "Brain", "Method")).toBe("Q-table");
  expect(find(sections, "Brain", "Network")).toBeUndefined();
  expect(find(sections, "Mazes", "Levels")).toBe("easy-01");
  expect(find(sections, "Learning", "Learning rate")).toBe("0.3");
  expect(sections.find((s) => s.title === "Result")).toBeUndefined();
});

test("missing or odd settings are left out and never throw", () => {
  expect(recipeSections({ bundle_version: 1, has_graph: false, config: {} }).length).toBeGreaterThanOrEqual(0);
  expect(() => recipeSections({ bundle_version: 1, has_graph: false, config: { dqn: 5, levels: "x" } })).not.toThrow();
});
