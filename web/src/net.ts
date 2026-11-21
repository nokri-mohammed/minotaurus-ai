// Talking to the game server (HTTP and WebSocket). `mockApi` plays a scripted run so the page can
// be tried without the server: open the page with ?mock=1.
import type { BrainInfo, LevelInfo, RunMessage } from "./protocol";
import { parseRunMessage } from "./protocol";

export type RunHandle = { close(): void };

export type Api = {
  levels(): Promise<LevelInfo[]>;
  uploadBrain(file: File): Promise<BrainInfo>;
  run(levelId: string, onMessage: (m: RunMessage) => void): RunHandle;
};

async function errorText(response: Response): Promise<string> {
  try {
    const body: { message?: string; detail?: string } = await response.json();
    return body.message ?? body.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

export const realApi: Api = {
  async levels() {
    const response = await fetch("/api/levels");
    if (!response.ok) throw new Error(await errorText(response));
    return response.json();
  },
  async uploadBrain(file) {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/brain", { method: "POST", body: form });
    if (!response.ok) throw new Error(await errorText(response));
    return response.json();
  },
  run(levelId, onMessage) {
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${scheme}://${location.host}/ws/run?level_id=${encodeURIComponent(levelId)}`);
    socket.onmessage = (event) => {
      const msg = typeof event.data === "string" ? parseRunMessage(event.data) : null;
      if (msg) onMessage(msg);
    };
    socket.onerror = () => onMessage({ type: "error", message: "Lost the connection to the server." });
    return { close: () => socket.close() };
  },
};

// ---- mock ----

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

export function chooseApi(): { api: Api; mock: boolean } {
  const mock = new URLSearchParams(location.search).has("mock");
  return { api: mock ? mockApi : realApi, mock };
}
