// WS /ws/run?level_id=<id>&brain_id=<id>: stream one run (run_started, tick..., result) of one brain.
import { type RunMessage, runMessageSchema } from "../../protocol";
import { type SocketHandle, apiService } from "../ApiService";

export function openRun(levelId: string, brainId: string, onMessage: (message: RunMessage) => void): SocketHandle {
  return apiService.socket(
    "/ws/run",
    { level_id: levelId, brain_id: brainId },
    runMessageSchema,
    onMessage,
    (message) => onMessage({ type: "error", message }),
  );
}
