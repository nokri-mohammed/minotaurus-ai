import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  AttemptsCharts, BatchPanel, Button, type Col, Confetti, DataTable, FileButton, LoadingOverlay, MazeCanvas, Panel, RecipePanel, Select, Stat, StatusPill, statusText,
} from "./components";
import { attemptColumns, secs } from "./components/attemptColumns";
import { type Attempt, attemptsOf, recentAttempts, summarize } from "./services/history";
import { type RunHandle, getBatches, getLevels, openRun, runAllLevels, saveAttempt, uploadBrain } from "./services";
import { brainOptions, shortId, withBrain } from "./brainOptions";
import type { BatchResult, BrainInfo, LevelInfo } from "./protocol";
import { atLeast } from "./minimumTime";
import { runButtonText } from "./runButton";
import { idleRun, reduceRun } from "./run";

const MIN_LOADING_MS = 3000; // the load is fast: keep the brain animation on screen until it has filled once

const COLUMNS = attemptColumns(false);

type Props = {
  attempts: Attempt[]; // every attempt of every brain, newest first
  onAttempts: (list: Attempt[]) => void;
  brains: BrainInfo[];
  onBrains: (list: BrainInfo[]) => void;
  brainId: string | null;
  onBrainId: (id: string | null) => void;
  hidden: boolean;
};

export function Arena({ attempts: allAttempts, onAttempts, brains, onBrains, brainId, onBrainId, hidden }: Props) {
  const [levels, setLevels] = useState<LevelInfo[] | null>(null);
  const [levelId, setLevelId] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [loadingBrain, setLoadingBrain] = useState(false);
  const [batches, setBatches] = useState<BatchResult[]>([]);
  const [batchWorking, setBatchWorking] = useState(false);
  const [run, dispatch] = useReducer(reduceRun, idleRun);
  const handle = useRef<RunHandle | null>(null);
  const saved = useRef(false);
  const [burst, setBurst] = useState(0); // goes up by one on every finish, to play the confetti

  const level = levels?.find((l) => l.id === levelId) ?? null;
  const brain = brains.find((b) => b.id === brainId) ?? null;
  // The page shows one brain at a time: only its attempts, charts and totals.
  const attempts = useMemo(() => attemptsOf(allAttempts, brainId), [allAttempts, brainId]);
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
    const attempt: Attempt = {
      id: crypto.randomUUID(), date: new Date().toISOString(), brainId: brain.id, brain: brain.name, method: brain.method,
      level: level.id, result: run.result.status, steps: run.result.steps, seconds: run.result.seconds,
      path,
    };
    onAttempts([attempt, ...allAttempts]);
    async function save() {
      try {
        await saveAttempt(attempt);
      } catch {
        setProblem("The attempt could not be saved on the server.");
      }
    }
    void save();
  }, [run.phase, run.result, run.trail, run.pos, brain, level, allAttempts, onAttempts]);

  // The earlier "run all levels" results belong to one brain, so they follow the selected brain.
  useEffect(() => {
    let current = true;
    setBatches([]);
    async function loadBatches() {
      if (brainId === null) return;
      try {
        const list = await getBatches(brainId);
        if (current) setBatches(list);
      } catch {
        // no earlier results: the panel just starts empty
      }
    }
    void loadBatches();
    return () => {
      current = false;
    };
  }, [brainId]);

  async function runAll() {
    if (!brain || batchWorking) return;
    setProblem(null);
    setBatchWorking(true);
    try {
      const batch = await runAllLevels(brain.id);
      setBatches([batch, ...batches]);
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Could not run all levels.");
    } finally {
      setBatchWorking(false);
    }
  }

  async function loadBrain(files: FileList | null) {
    const file = files?.[0];
    if (!file || loadingBrain) return;
    setProblem(null);
    setLoadingBrain(true);
    try {
      const info = await atLeast(uploadBrain(file), MIN_LOADING_MS);
      onBrains(withBrain(brains, info));
      onBrainId(info.id);
      dispatch({ type: "reset" });
    } catch (e) {
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
    if (!level || !brain) return;
    handle.current?.close();
    saved.current = false;
    setProblem(null);
    handle.current = openRun(level.id, brain.id, dispatch);
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
        : "Load a brain (.onnx or a .tar bundle) to begin.";

  return (
    <div id="arena" className="stack" hidden={hidden}>
      <Confetti burst={burst} />
      {loadingBrain && <LoadingOverlay text="Loading brain..." />}
      <header className="title-row">
        <div>
          <h1>Arena</h1>
          <p role="status" className="finding">{finding}</p>
        </div>
        <div className="actions">
          {brains.length > 0 && (
            <Select
              label="Brain"
              value={brainId}
              options={brainOptions(brains)}
              onChange={(id) => { onBrainId(id); dispatch({ type: "reset" }); }}
              isDisabled={running || loadingBrain}
            />
          )}
          <FileButton accept={[".onnx", ".tar"]} onFiles={loadBrain}>Load brain</FileButton>
        </div>
      </header>

      {problem && <p role="alert" className="problem">{problem}</p>}

      <div className="split">
        <Panel
          title={level ? level.name : "Maze"}
          note={brain ? `${brain.name} (${shortId(brain.id)})` : "No brain loaded"}
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
          <div className="run-row">
            <Button
              variant={running ? "secondary" : "primary"}
              onPress={running ? stop : start}
              isDisabled={!running && (!brain || !level || loadingBrain)}
            >
              {runButtonText(running)}
            </Button>
          </div>
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
            note={attempts.length === 0 ? "Saved for this brain." : `${attempts.length} runs of this brain`}
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
              <DataTable label="Past attempts" columns={COLUMNS} rows={recentAttempts(attempts)} rowId={(a) => a.id} empty="No attempts yet for this brain." />
            </div>
            {attempts.length > 0 && (
              <p className="muted attempts-more">
                {attempts.length > recentAttempts(attempts).length ? `Showing the latest ${recentAttempts(attempts).length}. ` : ""}
                <a href="#history">See all attempts and download logs</a>
              </p>
            )}
          </Panel>
        </div>
      </div>
      <BatchPanel brain={brain} batches={batches} working={batchWorking} onRun={runAll} disabled={!brain || running || loadingBrain || batchWorking} />
      <RecipePanel brain={brain} />
    </div>
  );
}
