import { Badge } from "@/components/ui/badge";
import type { AttemptStatus } from "../services/history";

const TEXT: Record<AttemptStatus, string> = {
  finished: "Finished", timed_out: "Timed out", stuck: "Stuck", stopped: "Stopped", error: "Error",
};
const TONE: Record<AttemptStatus, "positive" | "warning" | "secondary" | "destructive"> = {
  finished: "positive", timed_out: "warning", stuck: "warning", stopped: "secondary", error: "destructive",
};

export function statusText(status: AttemptStatus): string {
  return TEXT[status];
}

export function StatusPill({ status }: { status: AttemptStatus }) {
  return <Badge variant={TONE[status]}>{TEXT[status]}</Badge>;
}
