// Attempts live in the server's database, one list per brain.
import { type AttemptRecord, attemptRecordSchema, attemptsSchema, importResultSchema } from "../../protocol";
import { apiService } from "../ApiService";
import type { Attempt } from "../history";

export function toRecord(attempt: Attempt): AttemptRecord {
  const record: AttemptRecord = {
    id: attempt.id, date: attempt.date, brain_id: attempt.brainId, brain: attempt.brain, method: attempt.method,
    level: attempt.level, result: attempt.result, steps: attempt.steps, seconds: attempt.seconds,
  };
  if (attempt.path !== undefined) record.path = attempt.path;
  return record;
}

export function fromRecord(record: AttemptRecord): Attempt {
  const attempt: Attempt = {
    id: record.id, date: record.date, brainId: record.brain_id, brain: record.brain, method: record.method,
    level: record.level, result: record.result, steps: record.steps, seconds: record.seconds,
  };
  if (record.path) attempt.path = record.path;
  return attempt;
}

/** All attempts, newest first; or only those of one brain. */
export async function getAttempts(brainId?: string): Promise<Attempt[]> {
  const path = brainId ? `/api/attempts?brain_id=${brainId}` : "/api/attempts";
  const records = await apiService.get(path, attemptsSchema);
  const attempts: Attempt[] = [];
  for (const record of records) attempts.push(fromRecord(record));
  return attempts;
}

export async function saveAttempt(attempt: Attempt): Promise<void> {
  await apiService.postJson("/api/attempts", attemptRecordSchema, toRecord(attempt));
}

/** Send attempts saved in the browser before the database existed. Safe to repeat. */
export async function importAttempts(attempts: Attempt[]): Promise<number> {
  const records: AttemptRecord[] = [];
  for (const attempt of attempts) records.push(toRecord(attempt));
  const reply = await apiService.postJson("/api/attempts/import", importResultSchema, records);
  return reply.count;
}
