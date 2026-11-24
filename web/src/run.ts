// What the page shows during one run. A pure reducer: server messages in, display state out.
import type { Point, RunMessage } from "./protocol";
import type { AttemptStatus } from "./services/history";

export type RunState = {
  phase: "idle" | "running" | "done";
  pos: Point | null;
  trail: Point[]; // squares visited before the current one, oldest first
  steps: number;
  seconds: number; // game time, from the server
  stepLimit: number;
  result: { status: AttemptStatus; steps: number; seconds: number; message?: string } | null;
};

export const idleRun: RunState = {
  phase: "idle", pos: null, trail: [], steps: 0, seconds: 0, stepLimit: 0, result: null,
};

const TICK_SECONDS = 0.1;

// "stopped" comes from the Stop button, not from the server.
export type RunAction = RunMessage | { type: "reset" } | { type: "stopped" };

export function reduceRun(state: RunState, msg: RunAction): RunState {
  // A run that is over ignores late messages (a tick can still arrive just after a stop).
  if (state.phase === "done" && msg.type !== "reset" && msg.type !== "run_started") return state;
  switch (msg.type) {
    case "reset":
      return idleRun;
    case "run_started":
      return { ...idleRun, phase: "running", pos: msg.start, stepLimit: msg.step_limit };
    case "tick":
      return {
        ...state,
        trail: state.pos ? [...state.trail, state.pos] : state.trail,
        pos: { x: msg.x, y: msg.y },
        steps: msg.n,
        seconds: msg.n * TICK_SECONDS,
      };
    case "stopped":
      return { ...state, phase: "done", result: { status: "stopped", steps: state.steps, seconds: state.seconds } };
    case "result": {
      const { status, steps, seconds, message } = msg;
      return { ...state, phase: "done", result: message ? { status, steps, seconds, message } : { status, steps, seconds } };
    }
    case "error":
      return { ...state, phase: "done", result: { status: "error", steps: 0, seconds: 0, message: msg.message } };
  }
}
