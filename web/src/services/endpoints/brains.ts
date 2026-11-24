// GET /api/brains: every loaded brain. GET /api/brains/<id>/recipe: how a bundled brain was made.
import { type BrainRecipe, type BrainInfo, brainRecipeSchema, brainsSchema } from "../../protocol";
import { apiService } from "../ApiService";

export async function getBrains(): Promise<BrainInfo[]> {
  return apiService.get("/api/brains", brainsSchema);
}

export async function getBrainRecipe(brainId: string): Promise<BrainRecipe> {
  return apiService.get(`/api/brains/${brainId}/recipe`, brainRecipeSchema);
}

/** The training graph of a bundled brain: an image address for <img src>. */
export function brainGraphUrl(brainId: string): string {
  return `/api/brains/${brainId}/graph.png`;
}
