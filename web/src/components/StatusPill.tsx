import type { AttemptStatus } from "../services/history";

const TEXT: Record<AttemptStatus, string> = {
  finished: "Finished", timed_out: "Timed out", stuck: "Stuck", stopped: "Stopped", error: "Error",
};
const TONE: Record<AttemptStatus, string> = {
  finished: "positive", timed_out: "warning", stuck: "warning", stopped: "neutral", error: "negative",
};

export function statusText(status: AttemptStatus): string {
  return TEXT[status];
}

export function StatusPill({ status }: { status: AttemptStatus }) {
  return <span className={`pill pill-${TONE[status]}`}>{TEXT[status]}</span>;
}
