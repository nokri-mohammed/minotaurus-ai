import { expect, test } from "bun:test";
import samples from "../../data/schemas/message-samples.json";
import { brainInfoSchema, levelsSchema, runMessageSchema } from "./protocol";

test("every shared valid sample parses, every invalid one is rejected", () => {
  for (const s of samples.run_message.valid) expect(runMessageSchema.safeParse(s).success).toBe(true);
  for (const s of samples.run_message.invalid) expect(runMessageSchema.safeParse(s).success).toBe(false);
  for (const s of samples.levels_response.valid) expect(levelsSchema.safeParse(s).success).toBe(true);
  for (const s of samples.levels_response.invalid) expect(levelsSchema.safeParse(s).success).toBe(false);
  for (const s of samples.brain_response.valid) expect(brainInfoSchema.safeParse(s).success).toBe(true);
  for (const s of samples.brain_response.invalid) expect(brainInfoSchema.safeParse(s).success).toBe(false);
});
