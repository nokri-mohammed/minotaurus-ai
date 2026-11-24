// What the Brains page shows: one row per brain, a side-by-side compare, and the exam trend.
import { batchPercent } from "./batch";
import type { BatchResult, BrainInfo, BrainRecipe } from "./protocol";
import { recipeSections } from "./recipe";

type Json = Record<string, unknown>;

function asObject(value: unknown): Json | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) return value as Json;
  return null;
}

function generatedOf(recipe: BrainRecipe): Json | null {
  return asObject(asObject(recipe.config.levels)?.generated);
}

function sizesText(generated: Json): string {
  const sizes = generated.sizes;
  if (Array.isArray(sizes) && sizes.length > 0) return sizes.join(", ");
  return String(generated.size ?? "?");
}

/** Brains with the same key were tested on the same exam mazes. Null when the mazes are not generated. */
export function pileKey(recipe: BrainRecipe): string | null {
  const generated = generatedOf(recipe);
  if (!generated) return null;
  return JSON.stringify([generated.sizes ?? generated.size, generated.maze_seed, generated.test, generated.border_exit]);
}

/** Example: "sizes 9, 11, 13 / 120 exam". */
export function pileLabel(recipe: BrainRecipe): string {
  const generated = generatedOf(recipe);
  if (!generated) return "made levels";
  return `sizes ${sizesText(generated)} / ${generated.test} exam`;
}

export type BrainRow = {
  id: string;
  name: string;
  method: string;
  quiz: number | null;
  exam: number | null;
  portal: string;
  runAll: string;
  pile: string;
  network: string;
  learningRate: string;
  added: string;
};

function findValue(recipe: BrainRecipe, title: string, label: string): string {
  for (const section of recipeSections(recipe)) {
    if (section.title !== title) continue;
    for (const row of section.rows) {
      if (row.label === label) return row.value;
    }
  }
  return "–";
}

function portalText(recipe: BrainRecipe): string {
  const fixed = recipe.fixed_levels;
  if (!fixed) return "–";
  let done = 0;
  let all = 0;
  for (const finished of Object.values(fixed)) {
    all += 1;
    if (finished) done += 1;
  }
  return `${done} of ${all}`;
}

/** One table row. `recipe` is null for a plain .onnx brain; `batch` is its latest "run all levels". */
export function brainRow(brain: BrainInfo, recipe: BrainRecipe | null, batch: BatchResult | null): BrainRow {
  let runAll = "–";
  if (batch) runAll = `${batch.finished} of ${batch.total} (${batchPercent(batch)}%)`;
  return {
    id: brain.id,
    name: brain.name,
    method: brain.method,
    quiz: recipe?.scores ? recipe.scores.validation : null,
    exam: recipe?.scores ? recipe.scores.test : null,
    portal: recipe ? portalText(recipe) : "–",
    runAll,
    pile: recipe ? pileLabel(recipe) : "–",
    network: recipe ? findValue(recipe, "Brain", "Network") : "–",
    learningRate: recipe ? findValue(recipe, "Learning", "Learning rate") : "–",
    added: brain.added_at,
  };
}

export type CompareRow = { label: string; a: string; b: string };
export type Comparison = { settings: CompareRow[]; results: CompareRow[]; samePile: boolean };

function flatten(recipe: BrainRecipe): Map<string, string> {
  const flat = new Map<string, string>();
  for (const section of recipeSections(recipe)) {
    for (const row of section.rows) flat.set(`${section.title}: ${row.label}`, row.value);
  }
  return flat;
}

/** Settings that differ between two recipes, and their results side by side. */
export function compareRecipes(a: BrainRecipe, b: BrainRecipe): Comparison {
  const left = flatten(a);
  const right = flatten(b);
  const labels: string[] = [];
  for (const label of left.keys()) labels.push(label);
  for (const label of right.keys()) {
    if (!left.has(label)) labels.push(label);
  }
  const settings: CompareRow[] = [];
  const results: CompareRow[] = [];
  for (const label of labels) {
    const row = { label, a: left.get(label) ?? "–", b: right.get(label) ?? "–" };
    if (label.startsWith("Result: ")) {
      results.push(row);
    } else if (row.a !== row.b) {
      settings.push(row);
    }
  }
  return { settings, results, samePile: pileKey(a) === pileKey(b) };
}

export type TrendPoint = { id: string; name: string; date: string; exam: number };

/** Exam scores of the brains tested on one exam pile, oldest first. */
export function trendPoints(items: { brain: BrainInfo; recipe: BrainRecipe | null }[], key: string): TrendPoint[] {
  const points: TrendPoint[] = [];
  for (const item of items) {
    if (!item.recipe || !item.recipe.scores) continue;
    if (pileKey(item.recipe) !== key) continue;
    points.push({ id: item.brain.id, name: item.brain.name, date: item.brain.added_at, exam: item.recipe.scores.test });
  }
  points.sort((x, y) => x.date.localeCompare(y.date));
  return points;
}
