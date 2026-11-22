// What the rest of the page imports. `arenaApi` is the one object that components use; tests
// pass a fake with the same shape.
import { ApiService, type SocketHandle } from "./ApiService";
import { uploadBrain } from "./endpoints/brain";
import { getLevels } from "./endpoints/levels";
import { openRun } from "./endpoints/run";
import type { BrainInfo, LevelInfo, RunMessage } from "../protocol";

export type RunHandle = SocketHandle;

export type Api = {
  levels(): Promise<LevelInfo[]>;
  uploadBrain(file: File): Promise<BrainInfo>;
  run(levelId: string, onMessage: (message: RunMessage) => void): RunHandle;
};

const service = new ApiService();

export const arenaApi: Api = {
  levels: () => getLevels(service),
  uploadBrain: (file) => uploadBrain(service, file),
  run: (levelId, onMessage) => openRun(service, levelId, onMessage),
};
