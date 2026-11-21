// Every attempt is saved in the browser (localStorage). Storage can be missing or blocked, so all
// access is wrapped and the page works without it.
import type { ResultStatus } from "./protocol";

export type Attempt = {
  id: string;
  date: string; // ISO
  brain: string;
  method: string;
  level: string;
  result: ResultStatus;
  steps: number;
  seconds: number;
};

export type Store = Pick<Storage, "getItem" | "setItem">;
const KEY = "minotaurus.attempts.v1";

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
    (a.result === "finished" || a.result === "timed_out" || a.result === "error") &&
    typeof a.steps === "number" && typeof a.seconds === "number"
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
