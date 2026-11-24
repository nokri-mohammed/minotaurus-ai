import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  AttemptsCharts, BrainLoader, Button, type Col, Confetti, DataTable, FileButton, MazeCanvas, Panel, Select, Stat, StatusPill, statusText,
} from "./components";
import { downloadAttemptLog } from "./services/attemptLog";
import { type Attempt, addAttempt, loadAttempts, summarize } from "./services/history";
import { type RunHandle, getLevels, openRun, uploadBrain } from "./services";
import type { BrainInfo, LevelInfo } from "./protocol";
import { atLeast } from "./minimumTime";
import { runButtonText } from "./runButton";
import { idleRun, reduceRun } from "./run";

const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const secs = (n: number) => n.toFixed(1);
const MIN_LOADING_MS = 3000; // the load is fast: keep the brain animation on screen until it has filled once

const COLUMNS: Col<Attempt>[] = [
  { id: "date", header: "Date", primary: true, render: (a) => when(a.date) },
  { id: "brain", header: "Brain", render: (a) => a.brain },
  { id: "method", header: "Method", secondary: true, render: (a) => a.method },
  { id: "level", header: "Level", secondary: true, render: (a) => a.level },
  { id: "result", header: "Result", render: (a) => <StatusPill status={a.result} /> },
  { id: "steps", header: "Steps", align: "right", render: (a) => a.steps },
  { id: "time", header: "Time", align: "right", render: (a) => `${secs(a.seconds)} s` },
  {
    id: "log", header: "Log", secondary: true,
    render: (a) => (a.path ? <Button onPress={() => downloadAttemptLog(a)}>Download</Button> : "–"),
  },
];

export function Arena() {
  const [levels, setLevels] = useState<LevelInfo[] | null>(null);
  const [levelId, setLevelId] = useState<string | null>(null);
  const [brain, setBrain] = useState<BrainInfo | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [loadingBrain, setLoadingBrain] = useState(false);
  const [attempts, setAttempts] = useState<Attempt[]>(() => loadAttempts());
  const [run, dispatch] = useReducer(reduceRun, idleRun);
  const handle = useRef<RunHandle | null>(null);
  const saved = useRef(false);
  const [burst, setBurst] = useState(0); // goes up by one on every finish, to play the confetti

  const level = levels?.find((l) => l.id === levelId) ?? null;
  const summary = useMemo(() => summarize(attempts), [attempts]);

  useEffect(() => {
    async function loadLevels() {
      try {
        const list = await getLevels();
        setLevels(list);
        setLevelId(list[0]?.id ?? null);
      } catch {
        setLevels([]);
        setProblem("Cannot reach the arena. Start it with: uv run minotaurus dev (or try a scripted one: uv run minotaurus dev --mock)");
      }
    }
    void loadLevels();
    return () => handle.current?.close();
  }, []);

  useEffect(() => {
    if (run.phase !== "done" || !run.result || !brain || !level || saved.current) return;
    saved.current = true;
    if (run.result.status === "finished") setBurst((n) => n + 1);
    // Every square the brain stood on, start first: the squares before this one, then this one.
    const path: [number, number][] = [];
    for (const point of run.trail) path.push([point.x, point.y]);
    if (run.pos) path.push([run.pos.x, run.pos.y]);
    setAttempts(
      addAttempt({
        id: crypto.randomUUID(), date: new Date().toISOString(), brain: brain.name, method: brain.method,
        level: level.id, result: run.result.status, steps: run.result.steps, seconds: run.result.seconds,
        path,
      }),
    );
  }, [run.phase, run.result, run.trail, run.pos, brain, level]);

  async function loadBrain(files: FileList | null) {
    const file = files?.[0];
    if (!file || loadingBrain) return;
    setProblem(null);
    setLoadingBrain(true);
    try {
      setBrain(await atLeast(uploadBrain(file), MIN_LOADING_MS));
    } catch (e) {
      setBrain(null);
      setProblem(e instanceof Error ? e.message : "The brain was refused.");
    } finally {
      setLoadingBrain(false);
    }
  }

  function stop() {
    handle.current?.close();
    dispatch({ type: "stopped" });
  }

  function start() {
    if (!level) return;
    handle.current?.close();
    saved.current = false;
    setProblem(null);
    handle.current = openRun(level.id, dispatch);
  }

  const running = run.phase === "running";
  const done = run.phase === "done" ? run.result : null;
  const finding = loadingBrain
    ? "Loading brain..."
    : done
    ? done.status === "finished"
      ? `Finished in ${done.steps} steps, ${secs(done.seconds)} s.`
      : done.status === "timed_out"
        ? `Timed out after ${done.steps} steps. The limit on this level is ${run.stepLimit}.`
        : done.status === "stuck"
          ? `Stuck after ${done.steps} steps: ${done.message ?? "the brain is going in circles"}.`
          : done.status === "stopped"
            ? `Stopped after ${done.steps} steps.`
            : `The run failed: ${done.message ?? "unknown error"}.`
    : running
      ? "Running."
      : brain
        ? "Ready. Press Start run."
        : "Load a brain (.onnx) to begin.";

  return (
    <div id="arena" className="stack">
      <Confetti burst={burst} />
      <header className="title-row">
        <div>
          <h1>Arena</h1>
          <p role="status" className="finding">{loadingBrain && <BrainLoader />}{finding}</p>
        </div>
        <div className="actions">
          <FileButton accept={[".onnx"]} onFiles={loadBrain}>Load brain</FileButton>
          <Button
            variant={running ? "secondary" : "primary"}
            onPress={running ? stop : start}
            isDisabled={!running && (!brain || !level || loadingBrain)}
          >
            {runButtonText(running)}
          </Button>
        </div>
      </header>

      {problem && <p role="alert" className="problem">{problem}</p>}

      <div className="split">
        <Panel
          title={level ? level.name : "Maze"}
          note={brain ? `${brain.name} (${brain.method})` : "No brain loaded"}
          actions={
            levels && levels.length > 0 ? (
              <Select
                label="Level"
                value={levelId}
                options={levels.map((l) => ({ id: l.id, label: `${l.name} (${l.difficulty})`, group: l.group === "test" ? "Test mazes" : "Hand-made levels" }))}
                onChange={(id) => { setLevelId(id); dispatch({ type: "reset" }); }}
                isDisabled={running}
              />
            ) : undefined
          }
        >
          {levels === null ? <p className="empty">Loading levels...</p> : <MazeCanvas level={level} pos={run.pos} trail={run.trail} />}
        </Panel>

        <div className="right">
          <Panel title="This run" note={done ? statusText(done.status) : running ? "In progress" : "No run yet"}>
            <div className="stats">
              <Stat label="Steps" value={run.phase === "idle" ? "–" : String(run.steps)} unit={run.stepLimit ? `of ${run.stepLimit}` : undefined} />
              <Stat label="Game time" value={run.phase === "idle" ? "–" : secs(run.seconds)} unit="s" />
            </div>
          </Panel>

          <Panel
            title="Progress"
            note={attempts.length === 0 ? "Saved in this browser." : `${attempts.length} runs in this browser`}
          >
            <AttemptsCharts attempts={attempts} />
          </Panel>

          <Panel
            title="Past attempts"
            note={
              summary.total === 0
                ? "None yet."
                : `${summary.total} attempts, ${summary.finished} finished, best ${summary.bestSeconds === null ? "–" : `${secs(summary.bestSeconds)} s`}`
            }
            className="attempts"
          >
            <div id="attempts" className="scroll">
              <DataTable label="Past attempts" columns={COLUMNS} rows={attempts} rowId={(a) => a.id} empty="No attempts yet. Your runs are saved in this browser." />
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
