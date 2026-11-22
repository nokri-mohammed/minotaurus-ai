// The core of all server calls. It owns the rules: base URLs, fetch, error messages, zod
// validation of every reply and WebSocket frame. Endpoint files (services/endpoints/) only say
// WHICH path, WHICH schema and WHAT to do with the result.
import type { z } from "zod";
import { errorBodySchema } from "../protocol";

export class ApiError extends Error {}

export type SocketHandle = { close(): void };

type Deps = {
  baseUrl?: string; // HTTP origin, "" = same origin (the Vite proxy or the Python server)
  wsBase?: string; // WebSocket origin, default: same host as the page
  fetchFn?: typeof fetch;
  openSocket?: (url: string) => WebSocket;
};

export class ApiService {
  constructor(private readonly deps: Deps = {}) {}

  async get<T>(path: string, schema: z.ZodType<T>): Promise<T> {
    return this.request(path, schema);
  }

  async post<T>(path: string, schema: z.ZodType<T>, body: BodyInit): Promise<T> {
    return this.request(path, schema, { method: "POST", body });
  }

  /** Open a WebSocket. Frames that are not valid JSON matching `schema` are dropped. */
  socket<T>(
    path: string,
    query: Record<string, string>,
    schema: z.ZodType<T>,
    onMessage: (message: T) => void,
    onError: (message: string) => void,
  ): SocketHandle {
    const url = `${this.wsBase()}${path}?${new URLSearchParams(query).toString()}`;
    const socket = this.deps.openSocket ? this.deps.openSocket(url) : new WebSocket(url);
    socket.onmessage = (event) => {
      if (typeof event.data !== "string") return;
      try {
        const parsed = schema.safeParse(JSON.parse(event.data));
        if (parsed.success) onMessage(parsed.data);
      } catch {
        // not JSON: ignore the frame
      }
    };
    socket.onerror = () => onError("Lost the connection to the server.");
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
      return body.message ?? body.detail ?? (response.statusText || "The server refused the request.");
    } catch {
      return response.statusText || "The server refused the request.";
    }
  }
}
