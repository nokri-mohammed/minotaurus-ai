// A scripted run for trying the page without the game server: `bun run dev:mock`.
// Remove this file when the arena server (S3) is the only way to run.
import type { Api } from "./net";
import type { LevelInfo } from "./protocol";

const EASY_01 = ["#########", "#S..#...#", "#.#.#.#.#", "#.#...#.#", "#.#####.#", "#.....#.#", "###.#.#.#", "#...#...E", "#########"];
// Shortest path of easy-01 from the Python engine (start first).
const PATH: [number, number][] = [
  [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [2, 5], [3, 5], [4, 5], [5, 5], [5, 6], [5, 7], [6, 7], [7, 7], [8, 7],
];

const MOCK_LEVELS: LevelInfo[] = [
  { id: "easy-01", name: "First steps (mock)", difficulty: "easy", grid: EASY_01, step_limit: 52 },
  { id: "easy-01-short", name: "First steps, 6 step limit (mock, times out)", difficulty: "easy", grid: EASY_01, step_limit: 6 },
];

export const mockApi: Api = {
  async levels() {
    return MOCK_LEVELS;
  },
  async uploadBrain(file) {
    if (!file.name.endsWith(".onnx")) throw new Error("That is not an .onnx file.");
    return { name: file.name.replace(/\.onnx$/, ""), method: file.name.includes("dqn") ? "dqn" : "qtable" };
  },
  run(levelId, onMessage) {
    const level = MOCK_LEVELS.find((l) => l.id === levelId) ?? MOCK_LEVELS[0];
    const [sx, sy] = PATH[0];
    onMessage({ type: "run_started", level_id: level.id, start: { x: sx, y: sy }, step_limit: level.step_limit });
    let n = 0;
    const timer = setInterval(() => {
      n += 1;
      const [x, y] = PATH[n];
      onMessage({ type: "tick", n, x, y });
      if (n === level.step_limit || n === PATH.length - 1) {
        clearInterval(timer);
        const finished = n === PATH.length - 1;
        onMessage({ type: "result", status: finished ? "finished" : "timed_out", steps: n, seconds: n * 0.1 });
      }
    }, 100);
    return { close: () => clearInterval(timer) };
  },
};
