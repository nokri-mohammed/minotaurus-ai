// GET /api/levels: the levels the arena offers.
import { type LevelInfo, levelsSchema } from "../../protocol";
import { apiService } from "../ApiService";

export async function getLevels(): Promise<LevelInfo[]> {
  return apiService.get("/api/levels", levelsSchema);
}
