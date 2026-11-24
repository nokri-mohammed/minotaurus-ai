// Attempts live in the server's database (see services/endpoints/attempts.ts). This file keeps the
// Attempt type, small list helpers, and the one-time read of attempts an older version of the page
// saved in the browser (localStorage), so they can be sent to the server. Storage can be missing
// or blocked, so all access is wrapped.
import type { ResultStatus } from "../protocol";

// How an attempt ended: what the server says, or "stopped" (the Stop button; the page's own status).
export type AttemptStatus = ResultStatus | "stopped";

export type Attempt = {
  id: string;
  date: string; // ISO
  brainId: string; // the brain's sha256, or "unknown" for attempts saved before brains had ids
  brain: string; // the brain's name
  method: string;
  level: string;
  result: AttemptStatus;
  steps: number;
  seconds: number;
  path?: [number, number][]; // every square the brain stood on, start first (for the log download)
};

export const UNKNOWN_BRAIN = "unknown";

export type Store = Pick<Storage, "getItem" | "setItem">;
const KEY = "minotaurus.attempts.v1";
const MIGRATED_KEY = "minotaurus.attempts.migrated.v1";

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

function isOldAttempt(v: unknown): v is Omit<Attempt, "brainId"> & { brainId?: string } {
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

export const RECENT_ATTEMPTS = 10; // how many the Arena page lists; History lists all

/** The newest `count` attempts of a newest-first list. */
export function recentAttempts(list: Attempt[], count: number = RECENT_ATTEMPTS): Attempt[] {
  return list.slice(0, count);
}

/** The attempts of one brain, in the same order. */
export function attemptsOf(list: Attempt[], brainId: string | null): Attempt[] {
  const mine: Attempt[] = [];
  for (const attempt of list) {
    if (attempt.brainId === brainId) mine.push(attempt);
  }
  return mine;
}

/** Attempts saved in the browser by an older page, newest first; they get brainId "unknown". Never throws. */
export function loadLocalAttempts(store: Store | undefined = browserStore()): Attempt[] {
  try {
    const text = store?.getItem(KEY);
    if (!text) return [];
    const data: unknown = JSON.parse(text);
    if (!Array.isArray(data)) return [];
    const list: Attempt[] = [];
    for (const item of data) {
      if (isOldAttempt(item)) list.push({ ...item, brainId: item.brainId ?? UNKNOWN_BRAIN });
    }
    return list;
  } catch {
    return [];
  }
}

export function migrationDone(store: Store | undefined = browserStore()): boolean {
  try {
    return store?.getItem(MIGRATED_KEY) === "yes";
  } catch {
    return false;
  }
}

export function markMigrated(store: Store | undefined = browserStore()): void {
  try {
    store?.setItem(MIGRATED_KEY, "yes");
  } catch {
    // storage blocked: the import will simply run again next time (the server ignores repeats)
  }
}

export type Summary = { total: number; finished: number; bestSeconds: number | null };

export function summarize(list: Attempt[]): Summary {
  const times: number[] = [];
  for (const attempt of list) {
    if (attempt.result === "finished") times.push(attempt.seconds);
  }
  return {
    total: list.length,
    finished: times.length,
    bestSeconds: times.length ? Math.min(...times) : null,
  };
}
