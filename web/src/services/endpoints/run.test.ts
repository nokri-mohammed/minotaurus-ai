import { expect, test } from "bun:test";
import type { RunMessage } from "../../protocol";
import { ApiService } from "../ApiService";
import { openRun } from "./run";

class FakeSocket {
  onmessage: ((e: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  constructor(public url: string) {}
  close() { this.closed = true; }
}

test("openRun streams valid run messages and turns a lost connection into an error message", () => {
  let socket!: FakeSocket;
  const api = new ApiService({ wsBase: "ws://arena", openSocket: (url) => (socket = new FakeSocket(url)) as unknown as WebSocket });
  const got: RunMessage[] = [];
  const handle = openRun(api, "easy-01", (m) => got.push(m));
  expect(socket.url).toBe("ws://arena/ws/run?level_id=easy-01");
  socket.onmessage?.({ data: '{"type":"tick","n":1,"x":1,"y":2}' });
  socket.onmessage?.({ data: '{"type":"tick","n":"x"}' });
  expect(got).toEqual([{ type: "tick", n: 1, x: 1, y: 2 }]);
  socket.onerror?.();
  expect(got.at(-1)).toEqual({ type: "error", message: "Lost the connection to the server." });
  handle.close();
  expect(socket.closed).toBe(true);
});
