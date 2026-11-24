// Every attempt is saved in the browser (localStorage). Storage can be missing or blocked, so all
// access is wrapped and the page works without it.
import type { ResultStatus } from "../protocol";

// How an attempt ended: what the server says, or "stopped" (the Stop button; the page's own status).
export type AttemptStatus = ResultStatus | "stopped";

export type Attempt = {
  id: string;
  date: string; // ISO
  brain: string;
  method: string;
  level: string;
  result: AttemptStatus;
  steps: number;
  seconds: number;
  path?: [number, number][]; // every square the brain stood on, start first (for the log download)
};

export type Store = Pick<Storage, "getItem" | "setItem">;
const KEY = "minotaurus.attempts.v1";
const KEEP_PATHS = 30; // only the newest attempts keep their path, so the storage stays small

function isPath(v: unknown): boolean {
  if (v === undefined) return true;
  if (!Array.isArray(v)) return false;
  for (const point of v) {
    if (!Array.isArray(point) || point.length !== 2) return false;
    if (typeof point[0] !== "number" || typeof point[1] !== "number") return false;
  }
  return true;
}

export function browserStore(): Store | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

function isAttempt(v: unknown): v is Attempt {
  if (typeof v !== "object" || v === null) return false;
  const a = v as Record<string, unknown>;
  return (
    typeof a.id === "string" && typeof a.date === "string" && typeof a.brain === "string" &&
    typeof a.method === "string" && typeof a.level === "string" &&
    (a.result === "finished" || a.result === "timed_out" || a.result === "stuck" ||
      a.result === "stopped" || a.result === "error") &&
    typeof a.steps === "number" && typeof a.seconds === "number" && isPath(a.path)
  );
}

/** All saved attempts, newest first. Never throws. */
export function loadAttempts(store: Store | undefined = browserStore()): Attempt[] {
  try {
    const text = store?.getItem(KEY);
    if (!text) return [];
    const data: unknown = JSON.parse(text);
    return Array.isArray(data) ? data.filter(isAttempt) : [];
  } catch {
    return [];
  }
}

/** Save one attempt at the top of the list and return the new list. Never throws. */
export function addAttempt(attempt: Attempt, store: Store | undefined = browserStore()): Attempt[] {
  const list = [attempt, ...loadAttempts(store)];
  for (let i = KEEP_PATHS; i < list.length; i++) {
    if (list[i].path !== undefined) {
      const { path: _dropped, ...rest } = list[i];
      list[i] = rest;
    }
  }
  try {
    store?.setItem(KEY, JSON.stringify(list));
  } catch {
    // storage blocked or full: keep the list in memory only
  }
  return list;
}

export type Summary = { total: number; finished: number; bestSeconds: number | null };

export function summarize(list: Attempt[]): Summary {
  const times = list.filter((a) => a.result === "finished").map((a) => a.seconds);
  return {
    total: list.length,
    finished: times.length,
    bestSeconds: times.length ? Math.min(...times) : null,
  };
}
