// WS /ws/run?level_id=<id>: stream one run (run_started, tick..., result).
import { type RunMessage, runMessageSchema } from "../../protocol";
import { type SocketHandle, apiService } from "../ApiService";

export function openRun(levelId: string, onMessage: (message: RunMessage) => void): SocketHandle {
  return apiService.socket(
    "/ws/run",
    { level_id: levelId },
    runMessageSchema,
    onMessage,
    (message) => onMessage({ type: "error", message }),
  );
}
