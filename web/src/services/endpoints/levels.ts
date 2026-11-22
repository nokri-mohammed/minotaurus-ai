// GET /api/levels: the levels the arena offers.
import { type LevelInfo, levelsSchema } from "../../protocol";
import type { ApiService } from "../ApiService";

export async function getLevels(api: ApiService): Promise<LevelInfo[]> {
  return api.get("/api/levels", levelsSchema);
}
