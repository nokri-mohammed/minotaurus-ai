import { expect, test } from "bun:test";
import samples from "../../data/schemas/message-samples.json";
import {
  attemptRecordSchema, attemptsSchema, batchResultSchema, batchesSchema, brainInfoSchema, brainRecipeSchema, brainsSchema, levelsSchema, runMessageSchema,
} from "./protocol";

const checks = [
  ["run_message", runMessageSchema],
  ["levels_response", levelsSchema],
  ["brain_response", brainInfoSchema],
  ["brains_response", brainsSchema],
  ["brain_recipe", brainRecipeSchema],
  ["attempt", attemptRecordSchema],
  ["attempts_response", attemptsSchema],
  ["batch_result", batchResultSchema],
  ["batches_response", batchesSchema],
] as const;

test("every shared valid sample parses, every invalid one is rejected", () => {
  const all = samples as unknown as Record<string, { valid: unknown[]; invalid: unknown[] }>;
  for (const [name, schema] of checks) {
    for (const s of all[name].valid) expect(schema.safeParse(s).success).toBe(true);
    for (const s of all[name].invalid) expect(schema.safeParse(s).success).toBe(false);
  }
});
