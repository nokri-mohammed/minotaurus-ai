// Message types: the contract is data/schemas/messages.schema.json. The page never decides rules,
// it only reads these messages.

export type Point = { x: number; y: number };
export type Difficulty = "easy" | "medium" | "hard";
export type ResultStatus = "finished" | "timed_out" | "error";

export type RunMessage =
  | { type: "run_started"; level_id: string; start: Point; step_limit: number }
  | { type: "tick"; n: number; x: number; y: number }
  | { type: "result"; status: ResultStatus; steps: number; seconds: number; message?: string }
  | { type: "error"; message: string };

export type LevelInfo = {
  id: string;
  name: string;
  difficulty: Difficulty;
  grid: string[];
  step_limit: number;
};

export type BrainInfo = { name: string; method: "qtable" | "dqn" };

const isInt = (v: unknown): v is number => typeof v === "number" && Number.isInteger(v);
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const isPoint = (v: unknown): v is Point =>
  typeof v === "object" && v !== null && isInt((v as Point).x) && isInt((v as Point).y);

/** Parse one WebSocket text frame. Returns null when it is not a valid run message. */
export function parseRunMessage(text: string): RunMessage | null {
  let m: Record<string, unknown>;
  try {
    const raw: unknown = JSON.parse(text);
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
    m = raw as Record<string, unknown>;
  } catch {
    return null;
  }
  switch (m.type) {
    case "run_started":
      if (typeof m.level_id === "string" && isPoint(m.start) && isInt(m.step_limit)) {
        return { type: "run_started", level_id: m.level_id, start: m.start, step_limit: m.step_limit };
      }
      return null;
    case "tick":
      return isInt(m.n) && isInt(m.x) && isInt(m.y) ? { type: "tick", n: m.n, x: m.x, y: m.y } : null;
    case "result":
      if (
        (m.status === "finished" || m.status === "timed_out" || m.status === "error") &&
        isInt(m.steps) && isNum(m.seconds)
      ) {
        const out: RunMessage = { type: "result", status: m.status, steps: m.steps, seconds: m.seconds };
        if (typeof m.message === "string") out.message = m.message;
        return out;
      }
      return null;
    case "error":
      return typeof m.message === "string" ? { type: "error", message: m.message } : null;
    default:
      return null;
  }
}
