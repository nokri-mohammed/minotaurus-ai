import { expect, test } from "bun:test";
import { z } from "zod";
import { ApiError, ApiService } from "./ApiService";

const reply = (body: unknown, status = 200) =>
  (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;

const thing = z.object({ id: z.number() });

test("get returns data that matches the schema", async () => {
  const api = new ApiService({ fetchFn: reply({ id: 1 }) });
  expect(await api.get("/api/thing", thing)).toEqual({ id: 1 });
});

test("get rejects a reply that breaks the schema", async () => {
  const api = new ApiService({ fetchFn: reply({ id: "x" }) });
  await expect(api.get("/api/thing", thing)).rejects.toThrow("unexpected reply");
});

test("a failed request raises ApiError with the server's message or detail", async () => {
  for (const body of [{ message: "Brain too big" }, { detail: "Brain too big" }]) {
    const api = new ApiService({ fetchFn: reply(body, 413) });
    const error = await api.get("/api/thing", thing).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("Brain too big");
  }
});

test("a failed request with no body still raises ApiError", async () => {
  const fetchFn = (async () => new Response("oops", { status: 500, statusText: "Server Error" })) as unknown as typeof fetch;
  const error = await new ApiService({ fetchFn }).get("/x", thing).catch((e: unknown) => e);
  expect((error as ApiError).message).toBe("Server Error");
});

test("post sends the body with POST and the base url", async () => {
  let seen: { url: string; init?: RequestInit } | undefined;
  const fetchFn = (async (url: string, init?: RequestInit) => {
    seen = { url, init };
    return new Response(JSON.stringify({ id: 2 }));
  }) as unknown as typeof fetch;
  const form = new FormData();
  const api = new ApiService({ fetchFn, baseUrl: "http://arena" });
  expect(await api.post("/api/thing", thing, form)).toEqual({ id: 2 });
  expect(seen?.url).toBe("http://arena/api/thing");
  expect(seen?.init?.method).toBe("POST");
  expect(seen?.init?.body).toBe(form);
});

class FakeSocket {
  onmessage: ((e: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  constructor(public url: string) {}
  close() { this.closed = true; }
}

function socketApi() {
  const sockets: FakeSocket[] = [];
  const api = new ApiService({
    wsBase: "ws://arena",
    openSocket: (url) => {
      const s = new FakeSocket(url);
      sockets.push(s);
      return s as unknown as WebSocket;
    },
  });
  return { api, sockets };
}

test("socket validates every frame, ignores bad ones, reports errors and closes", () => {
  const { api, sockets } = socketApi();
  const got: unknown[] = [];
  const errors: string[] = [];
  const handle = api.socket("/ws/thing", { level_id: "a b" }, thing, (m) => got.push(m), (e) => errors.push(e));
  expect(sockets[0].url).toBe("ws://arena/ws/thing?level_id=a+b");
  sockets[0].onmessage?.({ data: '{"id":1}' });
  sockets[0].onmessage?.({ data: '{"id":"x"}' });
  sockets[0].onmessage?.({ data: "garbage" });
  sockets[0].onmessage?.({ data: new ArrayBuffer(1) });
  expect(got).toEqual([{ id: 1 }]);
  sockets[0].onerror?.();
  expect(errors).toEqual(["Lost the connection to the server."]);
  handle.close();
  expect(sockets[0].closed).toBe(true);
});

test("postJson sends the data as JSON and checks the reply", async () => {
  let seen: { init?: RequestInit } = {};
  const fetchFn = (async (_url: string, init?: RequestInit) => {
    seen = { init };
    return new Response(JSON.stringify({ id: 2 }));
  }) as unknown as typeof fetch;
  const api = new ApiService({ fetchFn });
  expect(await api.postJson("/api/thing", thing, { a: 1 })).toEqual({ id: 2 });
  expect(seen.init?.method).toBe("POST");
  expect(seen.init?.body).toBe('{"a":1}');
  expect((seen.init?.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
});
