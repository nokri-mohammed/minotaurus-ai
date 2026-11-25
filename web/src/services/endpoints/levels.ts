// GET /api/levels: the levels the arena offers. POST /api/mazes/random: a fresh random maze to watch.
import { type LevelInfo, type RandomMazeRequest, levelInfoSchema, levelsSchema, randomMazeRequestSchema } from "../../protocol";
import { apiService } from "../ApiService";

export async function getLevels(): Promise<LevelInfo[]> {
  return apiService.get("/api/levels", levelsSchema);
}

/** A fresh random maze of the asked size. It is only for watching and is not saved. */
export async function generateMaze(request: RandomMazeRequest): Promise<LevelInfo> {
  const checked = randomMazeRequestSchema.parse(request);
  return apiService.postJson("/api/mazes/random", levelInfoSchema, checked);
}
