// The only place the page talks to the game server. Every reply is validated with the zod
// schemas in protocol.ts, so a server that breaks the contract is caught here, not in the UI.
import type { z } from "zod";
import {
  type BrainInfo, type LevelInfo, type RunMessage, brainInfoSchema, errorBodySchema, levelsSchema,
  parseRunMessage,
} from "./protocol";

export type RunHandle = { close(): void };

/** What the page needs from a server. Arena depends on this, not on the class. */
export type Api = {
  levels(): Promise<LevelInfo[]>;
  uploadBrain(file: File): Promise<BrainInfo>;
  run(levelId: string, onMessage: (m: RunMessage) => void): RunHandle;
};

export class ApiError extends Error {}

type Deps = {
  baseUrl?: string; // HTTP origin, "" = same origin (the Vite proxy or the Python server)
  wsBase?: string; // WebSocket origin, default: same host as the page
  fetchFn?: typeof fetch;
  openSocket?: (url: string) => WebSocket;
};

export class ApiService implements Api {
  constructor(private readonly deps: Deps = {}) {}

  async levels(): Promise<LevelInfo[]> {
    return this.request("/api/levels", levelsSchema);
  }

  async uploadBrain(file: File): Promise<BrainInfo> {
    const form = new FormData();
    form.append("file", file);
    return this.request("/api/brain", brainInfoSchema, { method: "POST", body: form });
  }

  run(levelId: string, onMessage: (m: RunMessage) => void): RunHandle {
    const url = `${this.wsBase()}/ws/run?level_id=${encodeURIComponent(levelId)}`;
    const socket = this.deps.openSocket ? this.deps.openSocket(url) : new WebSocket(url);
    socket.onmessage = (event) => {
      const message = typeof event.data === "string" ? parseRunMessage(event.data) : null;
      if (message) onMessage(message);
    };
    socket.onerror = () => onMessage({ type: "error", message: "Lost the connection to the server." });
    return { close: () => socket.close() };
  }

  private wsBase(): string {
    if (this.deps.wsBase !== undefined) return this.deps.wsBase;
    return `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  }

  private async request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
    const fetchFn = this.deps.fetchFn ?? ((input, options) => fetch(input, options));
    const response = await fetchFn(`${this.deps.baseUrl ?? ""}${path}`, init);
    if (!response.ok) throw new ApiError(await this.errorText(response));
    const parsed = schema.safeParse(await response.json());
    if (!parsed.success) throw new ApiError("The server sent an unexpected reply.");
    return parsed.data;
  }

  private async errorText(response: Response): Promise<string> {
    try {
      const body = errorBodySchema.parse(await response.json());
      return body.message ?? body.detail ?? response.statusText;
    } catch {
      return response.statusText || "The server refused the request.";
    }
  }
}

export const apiService = new ApiService();
