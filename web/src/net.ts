// Talking to the game server (HTTP and WebSocket).
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

/** Picks the API once at start. The mock is a separate chunk, loaded only in `vite --mode mock`. */
export async function chooseApi(): Promise<{ api: Api; mock: boolean }> {
  if (import.meta.env.MODE === "mock") {
    const { mockApi } = await import("./mock");
    return { api: mockApi, mock: true };
  }
  return { api: realApi, mock: false };
}
