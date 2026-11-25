// What components import. Each function is one endpoint; the caller only passes its own
// arguments and never sees the ApiService behind it.
export type { SocketHandle as RunHandle } from "./ApiService";
export { uploadBrain } from "./endpoints/brain";
export { generateMaze, getLevels } from "./endpoints/levels";
export { openRun } from "./endpoints/run";
export { brainDownloadUrl, getBrainMetrics, getBrainRecipe, getBrains, verifyBrain } from "./endpoints/brains";
export { getBatches, runAllLevels } from "./endpoints/batches";
