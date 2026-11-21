import type { ResultStatus } from "../protocol";

const TEXT: Record<ResultStatus, string> = { finished: "Finished", timed_out: "Timed out", error: "Error" };
const TONE: Record<ResultStatus, string> = { finished: "positive", timed_out: "warning", error: "negative" };

export function statusText(status: ResultStatus): string {
  return TEXT[status];
}

export function StatusPill({ status }: { status: ResultStatus }) {
  return <span className={`pill pill-${TONE[status]}`}>{TEXT[status]}</span>;
}
