import { expect, test } from "bun:test";
import { ApiError, ApiService } from "./ApiService";
import type { LevelInfo, RunMessage } from "./protocol";

const LEVEL: LevelInfo = { id: "easy-01", name: "First steps", difficulty: "easy", grid: ["#S.E#"], step_limit: 8 };

const reply = (body: unknown, status = 200) =>
  (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;

test("levels returns validated data", async () => {
  const api = new ApiService({ fetchFn: reply([LEVEL]) });
  expect(await api.levels()).toEqual([LEVEL]);
});

test("levels rejects a reply that breaks the contract", async () => {
  const api = new ApiService({ fetchFn: reply([{ ...LEVEL, difficulty: "insane" }]) });
  await expect(api.levels()).rejects.toThrow("unexpected reply");
});

test("a failed request raises ApiError with the server's message", async () => {
  const api = new ApiService({ fetchFn: reply({ message: "Brain too big" }, 413) });
  const error = await api.levels().catch((e: unknown) => e);
  expect(error).toBeInstanceOf(ApiError);
  expect((error as ApiError).message).toBe("Brain too big");
});

test("uploadBrain posts the file as multipart form data", async () => {
  let seen: { url: string; init?: RequestInit } | undefined;
  const fetchFn = (async (url: string, init?: RequestInit) => {
    seen = { url, init };
    return new Response(JSON.stringify({ name: "q1", method: "qtable" }));
  }) as unknown as typeof fetch;
  const api = new ApiService({ fetchFn, baseUrl: "http://arena" });
  const brain = await api.uploadBrain(new File(["x"], "q1.onnx"));
  expect(brain).toEqual({ name: "q1", method: "qtable" });
  expect(seen?.url).toBe("http://arena/api/brain");
  expect(seen?.init?.method).toBe("POST");
  expect((seen?.init?.body as FormData).get("file")).toBeInstanceOf(File);
});

class FakeSocket {
  onmessage: ((e: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  constructor(public url: string) {}
  close() { this.closed = true; }
}

test("run opens the socket, passes only valid messages and can be closed", () => {
  let socket!: FakeSocket;
  const api = new ApiService({
    wsBase: "ws://arena",
    openSocket: (url) => (socket = new FakeSocket(url)) as unknown as WebSocket,
  });
  const got: RunMessage[] = [];
  const handle = api.run("easy-01", (m) => got.push(m));
  expect(socket.url).toBe("ws://arena/ws/run?level_id=easy-01");
  socket.onmessage?.({ data: '{"type":"tick","n":1,"x":1,"y":2}' });
  socket.onmessage?.({ data: '{"type":"tick","n":"x"}' }); // breaks the contract: ignored
  socket.onmessage?.({ data: "garbage" });
  expect(got).toEqual([{ type: "tick", n: 1, x: 1, y: 2 }]);
  socket.onerror?.();
  expect(got.at(-1)).toEqual({ type: "error", message: "Lost the connection to the server." });
  handle.close();
  expect(socket.closed).toBe(true);
});
