// The contract with the game server, as zod schemas. The language-neutral twin is
// data/schemas/messages.schema.json; data/schemas/message-samples.json is checked against both.
import { z } from "zod";

const coordinate = z.number().int().min(0);
const pointSchema = z.strictObject({ x: coordinate, y: coordinate });

export const difficultySchema = z.enum(["easy", "medium", "hard", "impossible"]);
export const resultStatusSchema = z.enum(["finished", "timed_out", "stuck", "error"]);

export const runMessageSchema = z.discriminatedUnion("type", [
  z.strictObject({
    type: z.literal("run_started"),
    level_id: z.string(),
    start: pointSchema,
    step_limit: z.number().int().min(1),
  }),
  z.strictObject({ type: z.literal("tick"), n: z.number().int().min(1), x: coordinate, y: coordinate }),
  z.strictObject({
    type: z.literal("result"),
    status: resultStatusSchema,
    steps: z.number().int().min(0),
    seconds: z.number().min(0),
    path_ratio: z.number().min(1).optional(),
    message: z.string().optional(),
  }),
  z.strictObject({ type: z.literal("error"), message: z.string() }),
]);

export const levelInfoSchema = z.strictObject({
  id: z.string(),
  name: z.string(),
  difficulty: difficultySchema,
  group: z.enum(["hand-made", "test"]).default("hand-made"),
  grid: z.array(z.string().regex(/^[#.SE]+$/)).min(1),
  step_limit: z.number().int().min(1),
});
export const levelsSchema = z.array(levelInfoSchema);

const hexId = z.string().regex(/^[0-9a-f]{64}$/);

// One loaded brain. `id` is the sha256 of its brain.onnx (the page shows the first 8 characters).
export const brainInfoSchema = z.strictObject({
  id: hexId,
  name: z.string(),
  method: z.enum(["qtable", "dqn"]),
  has_recipe: z.boolean(),
  added_at: z.string(),
});
export const brainsSchema = z.array(brainInfoSchema);

const share = z.number().min(0).max(1);

// What a bundle says about how its brain was made. `config` was checked by the server as a
// ConfigFile (data/schemas/brain-config.schema.json); the page only reads from it.
export const brainRecipeSchema = z.strictObject({
  bundle_version: z.number().int().min(1),
  config: z.record(z.string(), z.unknown()),
  scores: z.strictObject({ train: share, validation: share, test: share }).nullish(),
  fixed_levels: z.record(z.string(), z.boolean()).nullish(),
  test_stats: z.strictObject({ avg_steps: z.number().min(0), avg_path_ratio: z.number().min(1).nullish() }).nullish(),
  has_graph: z.boolean(),
});

// One "run all levels" of one brain: every portal level played at full speed.
export const levelResultSchema = z.strictObject({
  level_id: z.string(),
  name: z.string(),
  group: z.enum(["hand-made", "test"]),
  status: resultStatusSchema,
  steps: z.number().int().min(0),
  seconds: z.number().min(0),
  path_ratio: z.number().min(1).optional(),
});
export const batchResultSchema = z.strictObject({
  id: z.string().min(1).max(64),
  brain_id: hexId,
  date: z.string(),
  total: z.number().int().min(0),
  finished: z.number().int().min(0),
  results: z.array(levelResultSchema),
});
export const batchesSchema = z.array(batchResultSchema);
export const importResultSchema = z.strictObject({ count: z.number().int().min(0) });

export const errorBodySchema = z.object({ message: z.string().optional(), detail: z.string().optional() });

export type Point = z.infer<typeof pointSchema>;
export type Difficulty = z.infer<typeof difficultySchema>;
export type ResultStatus = z.infer<typeof resultStatusSchema>;
export type RunMessage = z.infer<typeof runMessageSchema>;
export type LevelInfo = z.infer<typeof levelInfoSchema>;
export type BrainInfo = z.infer<typeof brainInfoSchema>;
export type BrainRecipe = z.infer<typeof brainRecipeSchema>;
export type BatchResult = z.infer<typeof batchResultSchema>;
export type LevelResult = z.infer<typeof levelResultSchema>;
