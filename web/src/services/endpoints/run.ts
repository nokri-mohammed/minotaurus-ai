// WS /ws/run?level_id=<id>: stream one run (run_started, tick..., result).
import { type RunMessage, runMessageSchema } from "../../protocol";
import type { ApiService, SocketHandle } from "../ApiService";

export function openRun(api: ApiService, levelId: string, onMessage: (message: RunMessage) => void): SocketHandle {
  return api.socket(
    "/ws/run",
    { level_id: levelId },
    runMessageSchema,
    onMessage,
    (message) => onMessage({ type: "error", message }),
  );
}
