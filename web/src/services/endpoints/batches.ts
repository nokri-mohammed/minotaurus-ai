// POST /api/brains/<id>/run-all: play every portal level with one brain at full speed.
// GET /api/brains/<id>/batches: the earlier results of that brain, newest first.
import { type BatchResult, batchResultSchema, batchesSchema } from "../../protocol";
import { apiService } from "../ApiService";

export async function runAllLevels(brainId: string): Promise<BatchResult> {
  return apiService.post(`/api/brains/${brainId}/run-all`, batchResultSchema, "");
}

export async function getBatches(brainId: string): Promise<BatchResult[]> {
  return apiService.get(`/api/brains/${brainId}/batches`, batchesSchema);
}
