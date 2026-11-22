import { afterEach, beforeEach, expect, test } from "bun:test";
import type { RunMessage } from "../../protocol";
import { openRun } from "./run";

class FakeSocket {
  static last: FakeSocket;
  onmessage: ((e: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  constructor(public url: string) { FakeSocket.last = this; }
  close() { this.closed = true; }
}

const g = globalThis as unknown as Record<string, unknown>;
const saved = { WebSocket: g.WebSocket, location: g.location };
beforeEach(() => {
  g.WebSocket = FakeSocket;
  g.location = { protocol: "http:", host: "arena" };
});
afterEach(() => {
  g.WebSocket = saved.WebSocket;
  g.location = saved.location;
});

test("openRun streams valid run messages and turns a lost connection into an error message", () => {
  const got: RunMessage[] = [];
  const handle = openRun("easy-01", (m) => got.push(m));
  const socket = FakeSocket.last;
  expect(socket.url).toBe("ws://arena/ws/run?level_id=easy-01");
  socket.onmessage?.({ data: '{"type":"tick","n":1,"x":1,"y":2}' });
  socket.onmessage?.({ data: '{"type":"tick","n":"x"}' });
  expect(got).toEqual([{ type: "tick", n: 1, x: 1, y: 2 }]);
  socket.onerror?.();
  expect(got.at(-1)).toEqual({ type: "error", message: "Lost the connection to the server." });
  handle.close();
  expect(socket.closed).toBe(true);
});
