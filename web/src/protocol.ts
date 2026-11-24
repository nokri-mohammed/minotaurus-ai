// The contract with the game server, as zod schemas. The language-neutral twin is
// data/schemas/messages.schema.json; data/schemas/message-samples.json is checked against both.
import { z } from "zod";

const coordinate = z.number().int().min(0);
const pointSchema = z.strictObject({ x: coordinate, y: coordinate });

export const difficultySchema = z.enum(["easy", "medium", "hard", "impossible"]);
export const resultStatusSchema = z.enum(["finished", "timed_out", "error"]);

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

export const brainInfoSchema = z.strictObject({ name: z.string(), method: z.enum(["qtable", "dqn"]) });

export const errorBodySchema = z.object({ message: z.string().optional(), detail: z.string().optional() });

export type Point = z.infer<typeof pointSchema>;
export type Difficulty = z.infer<typeof difficultySchema>;
export type ResultStatus = z.infer<typeof resultStatusSchema>;
export type RunMessage = z.infer<typeof runMessageSchema>;
export type LevelInfo = z.infer<typeof levelInfoSchema>;
export type BrainInfo = z.infer<typeof brainInfoSchema>;
