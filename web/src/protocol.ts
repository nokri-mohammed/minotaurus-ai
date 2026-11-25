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
  group: z.enum(["hand-made", "test", "random"]).default("hand-made"),
  grid: z.array(z.string().regex(/^[#.SE]+$/)).min(1),
  step_limit: z.number().int().min(1),
});
export const levelsSchema = z.array(levelInfoSchema);

/** What the page sends to ask for a random maze. */
export const randomMazeRequestSchema = z.strictObject({
  size: z.number().int(),
  seed: z.number().int().min(0).max(999999).optional(),
  random_start: z.boolean().optional(),
  border_exit: z.boolean().optional(),
});

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
  signed_by: z.string().regex(/^[0-9a-f]{16}$/).nullish(),
  author_first_seen: z.string().nullish(),
});

// The training curves of a bundled brain, read from the metrics.jsonl in its bundle. A value the
// run did not record is left out, not null.
export const brainMetricsSchema = z.strictObject({
  points: z.array(
    z.strictObject({
      episode: z.number().int().min(0),
      success_rate: share.optional(),
      avg_steps: z.number().min(0).optional(),
      avg_reward: z.number().optional(),
      epsilon: share.optional(),
      loss: z.number().min(0).optional(),
    }),
  ),
  quiz: z.array(z.strictObject({ episode: z.number().int().min(0), validation_success: share })),
  saved_at: z.number().int().min(0).optional(),
});

// The server played a bundled brain again and compared with the scores its bundle claims.
export const verificationSchema = z.strictObject({
  status: z.enum(["verified", "mismatch", "unavailable"]),
  message: z.string(),
  checks: z.array(
    z.strictObject({
      name: z.string(),
      claimed: z.number().optional(),
      actual: z.number().optional(),
      match: z.boolean(),
    }),
  ),
  not_checked: z.array(z.string()),
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
export type RandomMazeRequest = z.infer<typeof randomMazeRequestSchema>;
export type BrainInfo = z.infer<typeof brainInfoSchema>;
export type BrainRecipe = z.infer<typeof brainRecipeSchema>;
export type BrainMetrics = z.infer<typeof brainMetricsSchema>;
export type Verification = z.infer<typeof verificationSchema>;
export type BatchResult = z.infer<typeof batchResultSchema>;
export type LevelResult = z.infer<typeof levelResultSchema>;
