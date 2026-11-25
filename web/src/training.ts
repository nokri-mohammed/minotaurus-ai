// Turns the server's training metrics into rows for the charts: one row per try number.
import type { BrainMetrics } from "./protocol";

export type CurveRow = {
  episode: number;
  success_rate?: number;
  avg_steps?: number;
  avg_reward?: number;
  epsilon?: number;
  loss?: number;
  validation_success?: number; // the quiz score at this try
};

/** Training lines and quiz checks merged by try number, oldest first. */
export function mergeCurves(metrics: Pick<BrainMetrics, "points" | "quiz">): CurveRow[] {
  const byEpisode = new Map<number, CurveRow>();
  for (const point of metrics.points) {
    const row = byEpisode.get(point.episode) ?? { episode: point.episode };
    byEpisode.set(point.episode, { ...row, ...point });
  }
  for (const check of metrics.quiz) {
    const row = byEpisode.get(check.episode) ?? { episode: check.episode };
    byEpisode.set(check.episode, { ...row, validation_success: check.validation_success });
  }
  const rows: CurveRow[] = [];
  for (const row of byEpisode.values()) rows.push(row);
  rows.sort((a, b) => a.episode - b.episode);
  return rows;
}

/** True when at least one row has a value for this curve. */
export function hasCurve(rows: CurveRow[], key: keyof CurveRow): boolean {
  for (const row of rows) {
    if (row[key] !== undefined) return true;
  }
  return false;
}
