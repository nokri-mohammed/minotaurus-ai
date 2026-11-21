import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  Button, type Col, DataTable, FileButton, MazeCanvas, Panel, Select, Stat, StatusPill, statusText,
} from "./components";
import { type Attempt, addAttempt, loadAttempts, summarize } from "./history";
import type { Api, RunHandle } from "./net";
import type { BrainInfo, LevelInfo } from "./protocol";
import { idleRun, reduceRun } from "./run";

const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const secs = (n: number) => n.toFixed(1);

const COLUMNS: Col<Attempt>[] = [
  { id: "date", header: "Date", primary: true, render: (a) => when(a.date) },
  { id: "brain", header: "Brain", render: (a) => a.brain },
  { id: "method", header: "Method", secondary: true, render: (a) => a.method },
  { id: "level", header: "Level", secondary: true, render: (a) => a.level },
  { id: "result", header: "Result", render: (a) => <StatusPill status={a.result} /> },
  { id: "steps", header: "Steps", align: "right", render: (a) => a.steps },
  { id: "time", header: "Time", align: "right", render: (a) => `${secs(a.seconds)} s` },
];

export function Arena({ api }: { api: Api }) {
  const [levels, setLevels] = useState<LevelInfo[] | null>(null);
  const [levelId, setLevelId] = useState<string | null>(null);
  const [brain, setBrain] = useState<BrainInfo | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [attempts, setAttempts] = useState<Attempt[]>(() => loadAttempts());
  const [run, dispatch] = useReducer(reduceRun, idleRun);
  const handle = useRef<RunHandle | null>(null);
  const saved = useRef(false);

  const level = levels?.find((l) => l.id === levelId) ?? null;
  const summary = useMemo(() => summarize(attempts), [attempts]);

  useEffect(() => {
    api.levels().then(
      (list) => {
        setLevels(list);
        setLevelId(list[0]?.id ?? null);
      },
      () => {
        setLevels([]);
        setProblem("Cannot reach the server. Start it with: uv run minotaurus dev");
      },
    );
    return () => handle.current?.close();
  }, [api]);

  useEffect(() => {
    if (run.phase !== "done" || !run.result || !brain || !level || saved.current) return;
    saved.current = true;
    setAttempts(
      addAttempt({
        id: crypto.randomUUID(), date: new Date().toISOString(), brain: brain.name, method: brain.method,
        level: level.id, result: run.result.status, steps: run.result.steps, seconds: run.result.seconds,
      }),
    );
  }, [run.phase, run.result, brain, level]);

  async function loadBrain(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setProblem(null);
    try {
      setBrain(await api.uploadBrain(file));
    } catch (e) {
      setBrain(null);
      setProblem(e instanceof Error ? e.message : "The brain was refused.");
    }
  }

  function start() {
    if (!level) return;
    handle.current?.close();
    saved.current = false;
    setProblem(null);
    handle.current = api.run(level.id, dispatch);
  }

  const running = run.phase === "running";
  const done = run.phase === "done" ? run.result : null;
  const finding = done
    ? done.status === "finished"
      ? `Finished in ${done.steps} steps, ${secs(done.seconds)} s.`
      : done.status === "timed_out"
        ? `Timed out after ${done.steps} steps. The limit on this level is ${run.stepLimit}.`
        : `The run failed: ${done.message ?? "unknown error"}.`
    : running
      ? "Running."
      : brain
        ? "Ready. Press Start run."
        : "Load a brain (.onnx) to begin.";

  return (
    <div id="arena" className="stack">
      <header className="title-row">
        <div>
          <h1>Arena</h1>
          <p role="status" className="finding">{finding}</p>
        </div>
        <div className="actions">
          <FileButton accept={[".onnx"]} onFiles={loadBrain}>Load brain</FileButton>
          <Button variant="primary" onPress={start} isDisabled={!brain || !level || running}>Start run</Button>
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
                options={levels.map((l) => ({ id: l.id, label: `${l.name} (${l.difficulty})` }))}
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
