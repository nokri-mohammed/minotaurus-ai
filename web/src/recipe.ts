// A brain's recipe in plain words: the training config and the result of a bundle, grouped.
import type { BrainRecipe } from "./protocol";

export type RecipeRow = { label: string; value: string };
export type RecipeSection = { title: string; rows: RecipeRow[] };

type Json = Record<string, unknown>;

function asObject(value: unknown): Json | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) return value as Json;
  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return null;
}

function joinNumbers(value: unknown, separator: string): string | null {
  if (!Array.isArray(value) || value.length === 0) return null;
  const parts: string[] = [];
  for (const item of value) parts.push(String(item));
  return parts.join(separator);
}

const percent = (share: number) => `${Math.round(share * 100)}%`;

function add(rows: RecipeRow[], label: string, value: string | null) {
  if (value !== null) rows.push({ label, value });
}

function mazes(config: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  const levels = config.levels;
  const generated = asObject(asObject(levels)?.generated);
  if (generated) {
    const sizes = joinNumbers(generated.sizes, ", ");
    add(rows, "Sizes", sizes ?? (asNumber(generated.size) !== null ? String(generated.size) : null));
    const train = asNumber(generated.train);
    const validation = asNumber(generated.validation);
    const test = asNumber(generated.test);
    if (train !== null && validation !== null && test !== null) {
      add(rows, "Piles", `${train} practice, ${validation} quiz, ${test} exam`);
    }
    const mazeSeed = asNumber(generated.maze_seed);
    add(rows, "Maze seed", mazeSeed !== null ? String(mazeSeed) : null);
    if (generated.border_exit === true) add(rows, "Exit", "in the outer wall");
  } else {
    add(rows, "Levels", joinNumbers(levels, ", "));
  }
  return rows;
}

function brainRows(config: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  if (config.method === "dqn") add(rows, "Method", "DQN");
  if (config.method === "qtable") add(rows, "Method", "Q-table");
  const dqn = asObject(config.dqn);
  add(rows, "Network", dqn ? joinNumbers(dqn.hidden_layers, " × ") : null);
  const seed = asNumber(config.seed);
  add(rows, "Seed", seed !== null ? String(seed) : null);
  if (config.wall_mask === true) add(rows, "Wall mask", "on (never walks into a wall it sees)");
  return rows;
}

function learningBlock(config: Json): Json | null {
  return asObject(config.dqn) ?? asObject(config.qtable);
}

function learningRows(block: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  const pairs: [string, string][] = [
    ["Learning rate", "learning_rate"],
    ["Batch size", "batch_size"],
    ["Discount", "gamma"],
    ["Memory", "replay_size"],
  ];
  for (const [label, key] of pairs) {
    const value = asNumber(block[key]);
    add(rows, label, value !== null ? String(value) : null);
  }
  const update = asNumber(block.target_update);
  add(rows, "Target update", update !== null ? `every ${update} steps` : null);
  return rows;
}

function exploringRows(block: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  const start = asNumber(block.epsilon_start);
  const end = asNumber(block.epsilon_end);
  const decay = asNumber(block.epsilon_decay);
  if (start !== null && end !== null && decay !== null) {
    const fall = Math.round((1 - decay) * 1000) / 10;
    add(rows, "Random moves", `${percent(start)} down to ${percent(end)}, ${fall}% less per try`);
  }
  return rows;
}

function rewardRows(block: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  if (block.shaping === true) add(rows, "Shaping", "on");
  const novelty = asNumber(block.novelty_bonus);
  const revisit = asNumber(block.revisit_penalty);
  if (novelty !== null && novelty > 0) add(rows, "Novelty bonus", String(novelty));
  if (revisit !== null && revisit > 0) add(rows, "Revisit penalty", String(revisit));
  return rows;
}

function trainingRows(config: Json): RecipeRow[] {
  const rows: RecipeRow[] = [];
  const episodes = asNumber(config.episodes);
  add(rows, "Tries", episodes !== null ? `up to ${episodes}` : null);
  const every = asNumber(config.eval_every);
  add(rows, "Quiz", every !== null ? `every ${every} tries` : null);
  const patience = asNumber(config.patience);
  if (patience !== null) add(rows, "Early stop", `after ${patience} quizzes without gain`);
  return rows;
}

function resultRows(recipe: BrainRecipe): RecipeRow[] {
  const rows: RecipeRow[] = [];
  if (recipe.scores) {
    add(rows, "Quiz (validation)", percent(recipe.scores.validation));
    add(rows, "Exam (test)", percent(recipe.scores.test));
  }
  if (recipe.fixed_levels) {
    let done = 0;
    let all = 0;
    for (const finished of Object.values(recipe.fixed_levels)) {
      all += 1;
      if (finished) done += 1;
    }
    add(rows, "Portal levels", `${done} of ${all} finished`);
  }
  const ratio = recipe.test_stats?.avg_path_ratio;
  if (ratio !== undefined && ratio !== null) add(rows, "Route length", `${ratio.toFixed(2)} times the shortest`);
  return rows;
}

/** The recipe as titled groups of label and value; empty groups are left out. Never throws. */
export function recipeSections(recipe: BrainRecipe): RecipeSection[] {
  const config = recipe.config;
  const block = learningBlock(config);
  const sections: RecipeSection[] = [
    { title: "Mazes", rows: mazes(config) },
    { title: "Brain", rows: brainRows(config) },
    { title: "Learning", rows: block ? learningRows(block) : [] },
    { title: "Exploring", rows: block ? exploringRows(block) : [] },
    { title: "Rewards", rows: block ? rewardRows(block) : [] },
    { title: "Training", rows: trainingRows(config) },
    { title: "Result", rows: resultRows(recipe) },
  ];
  const shown: RecipeSection[] = [];
  for (const section of sections) {
    if (section.rows.length > 0) shown.push(section);
  }
  return shown;
}
