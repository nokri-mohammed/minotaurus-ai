// GET /api/brains: every loaded brain. GET /api/brains/<id>/recipe: how a bundled brain was made.
import {
  type BrainMetrics, type BrainRecipe, type BrainInfo, brainMetricsSchema, brainRecipeSchema, brainsSchema,
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
