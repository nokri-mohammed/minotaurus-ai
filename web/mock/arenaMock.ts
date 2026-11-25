// A fake arena server that lives inside the Vite dev server (`bun run dev:mock`), so the page is
// the same code with or without it. Same contract as data/schemas/messages.schema.json:
//   GET /api/levels, POST /api/brain, WS /ws/run?level_id=<id>
// Delete this folder when the real arena server (stage S3) exists.
import { createHash } from "node:crypto";
import type { IncomingMessage } from "node:http";
import type { Duplex } from "node:stream";
import type { Plugin } from "vite";

const EASY_01 = ["#########", "#S..#...#", "#.#.#.#.#", "#.#...#.#", "#.#####.#", "#.....#.#", "###.#.#.#", "#...#...E", "#########"];
// Shortest path of easy-01 from the Python engine (start first).
const PATH: [number, number][] = [
  [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [2, 5], [3, 5], [4, 5], [5, 5], [5, 6], [5, 7], [6, 7], [7, 7], [8, 7],
];
const LEVELS = [
  { id: "easy-01", name: "First steps", difficulty: "easy", grid: EASY_01, step_limit: 52 },
  { id: "easy-01-short", name: "First steps, 6 step limit (times out)", difficulty: "easy", grid: EASY_01, step_limit: 6 },
];
const GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

/** One unmasked server-to-client text frame. */
function frame(text: string): Buffer {
  const body = Buffer.from(text);
  const head = body.length < 126 ? Buffer.from([0x81, body.length]) : Buffer.from([0x81, 126, body.length >> 8, body.length & 255]);
  return Buffer.concat([head, body]);
}

function run(socket: Duplex, levelId: string): void {
  const level = LEVELS.find((l) => l.id === levelId) ?? LEVELS[0];
  const send = (m: object) => socket.write(frame(JSON.stringify(m)));
  send({ type: "run_started", level_id: level.id, start: { x: PATH[0][0], y: PATH[0][1] }, step_limit: level.step_limit });
  let n = 0;
  const timer = setInterval(() => {
    n += 1;
    send({ type: "tick", n, x: PATH[n][0], y: PATH[n][1] });
    if (n === level.step_limit || n === PATH.length - 1) {
      clearInterval(timer);
      const finished = n === PATH.length - 1;
      send({ type: "result", status: finished ? "finished" : "timed_out", steps: n, seconds: Math.round(n) / 10 });
    }
  }, 100);
  socket.on("close", () => clearInterval(timer));
  socket.on("error", () => clearInterval(timer));
}

// The mock keeps brains in memory (they are gone when the Vite server stops).
const mockBrains: { id: string; name: string; method: string; has_recipe: boolean; added_at: string }[] = [];

function mockId(name: string): string {
  return createHash("sha256").update(name).digest("hex");
}

export function arenaMock(): Plugin {
  return {
    name: "minotaurus-arena-mock",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const path = (req.url ?? "").split("?")[0];
        const json = (code: number, body: unknown) => {
          res.statusCode = code;
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify(body));
        };
        if (req.method === "GET" && path === "/api/levels") return json(200, LEVELS);
        if (req.method === "POST" && path === "/api/brain") {
          const chunks: Buffer[] = [];
          req.on("data", (c: Buffer) => chunks.push(c));
          req.on("end", () => {
            const name = /filename="([^"]+)"/.exec(Buffer.concat(chunks).toString("latin1"))?.[1] ?? "";
            if (!name.endsWith(".onnx")) return json(400, { message: "That is not an .onnx file." });
            const brain = {
              id: mockId(name), name: name.replace(/\.onnx$/, ""), method: name.includes("dqn") ? "dqn" : "qtable",
              has_recipe: false, added_at: new Date().toISOString(),
            };
            const index = mockBrains.findIndex((b) => b.id === brain.id);
            if (index >= 0) mockBrains.splice(index, 1);
            mockBrains.unshift(brain);
            json(200, brain);
          });
          return;
        }
        if (req.method === "GET" && path === "/api/brains") return json(200, mockBrains);
        next();
      });
      server.httpServer?.on("upgrade", (req: IncomingMessage, socket: Duplex) => {
        const url = new URL(req.url ?? "", "http://localhost");
        const key = req.headers["sec-websocket-key"];
        if (url.pathname !== "/ws/run" || typeof key !== "string") return; // leave Vite's own sockets alone
        const accept = createHash("sha1").update(key + GUID).digest("base64");
        socket.write(`HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ${accept}\r\n\r\n`);
        run(socket, url.searchParams.get("level_id") ?? "");
      });
    },
  };
}
