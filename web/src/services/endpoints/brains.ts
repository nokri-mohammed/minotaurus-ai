// GET /api/brains: every loaded brain. GET /api/brains/<id>/recipe: how a bundled brain was made.
import {
  type BrainMetrics, type BrainRecipe, type BrainInfo, type Verification, brainMetricsSchema, brainRecipeSchema,
  brainsSchema, verificationSchema,
} from "../../protocol";
import { apiService } from "../ApiService";

export async function getBrains(): Promise<BrainInfo[]> {
  return apiService.get("/api/brains", brainsSchema);
}

export async function getBrainRecipe(brainId: string): Promise<BrainRecipe> {
  return apiService.get(`/api/brains/${brainId}/recipe`, brainRecipeSchema);
}

/** The training curves of a bundled brain, to draw as charts. */
export async function getBrainMetrics(brainId: string): Promise<BrainMetrics> {
  return apiService.get(`/api/brains/${brainId}/metrics`, brainMetricsSchema);
}

/** Ask the server to play the brain again on its exam mazes and compare with the bundle's scores. */
export async function verifyBrain(brainId: string): Promise<Verification> {
  return apiService.post(`/api/brains/${brainId}/verify`, verificationSchema, "");
}
