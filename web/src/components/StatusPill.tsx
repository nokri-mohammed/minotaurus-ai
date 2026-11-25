import { Badge } from "@/components/ui/badge";
import type { RunStatus } from "../run";

const TEXT: Record<RunStatus, string> = {
  finished: "Finished", timed_out: "Timed out", stuck: "Stuck", stopped: "Stopped", error: "Error",
};
const TONE: Record<RunStatus, "positive" | "warning" | "secondary" | "destructive"> = {
  finished: "positive", timed_out: "warning", stuck: "warning", stopped: "secondary", error: "destructive",
};

export function statusText(status: RunStatus): string {
  return TEXT[status];
}

export function StatusPill({ status }: { status: RunStatus }) {
  return <Badge variant={TONE[status]}>{TEXT[status]}</Badge>;
}
