import { useEffect, useReducer, useRef, useState } from "react";
import {
  BatchPanel, Confetti, DownloadButton, FileButton, RatingPanel, LoadingOverlay, MazeCanvas, Panel, RecipePanel, Select, Stat, StatusPill, statusText,
} from "./components";
import { type RunHandle, getBatches, getLevels, openRun, runAllLevels, uploadBrain } from "./services";
import { brainOptions, shortId, withBrain } from "./brainOptions";
import type { BatchResult, BrainInfo, LevelInfo } from "./protocol";
import { batchSummary } from "./batch";
import { atLeast } from "./minimumTime";
import { runLedLabel } from "./runButton";
import { idleRun, reduceRun, resultSentence } from "./run";

const MIN_LOADING_MS = 3000; // the load is fast: keep the brain animation on screen until it has filled once

type Props = {
  brains: BrainInfo[];
  onBrains: (list: BrainInfo[]) => void;
  brainId: string | null;
  onBrainId: (id: string | null) => void;
  hidden: boolean;
};

function groupName(group: LevelInfo["group"]): string {
  if (group === "test") return "Test mazes";
  return "Hand-made levels";
}

// The dropdown lists the hand-made levels only; test mazes stay in "run all levels".
function levelOptions(levels: LevelInfo[]) {
  const options: { id: string; label: string; group: string }[] = [];
  for (const l of levels) {
    if (l.group === "test") continue;
    options.push({ id: l.id, label: `${l.name} (${l.difficulty})`, group: groupName(l.group) });
  }
  return options;
}

export function Arena({ brains, onBrains, brainId, onBrainId, hidden }: Props) {
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

  // A manual run is only for watching: it is not saved. The "run all levels" result is the record.
  useEffect(() => {
    if (run.phase !== "done" || !run.result || saved.current) return;
    saved.current = true;
    if (run.result.status === "finished") setBurst((n) => n + 1);
  }, [run.phase, run.result]);

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
      setBatches([batch]);
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Could not run all levels.");
    } finally {
      setBatchWorking(false);
    }
  }

  // A brain that has no "run all levels" result yet gets one when it is loaded, so it has a score at once.
  async function scoreNewBrain(id: string) {
    try {
      const known = await getBatches(id);
      if (known.length === 0) await runAllLevels(id);
    } catch {
      // no score now: the All levels panel still has its button
    }
  }

  async function loadBrain(files: FileList | null) {
    const file = files?.[0];
    if (!file || loadingBrain) return;
    setProblem(null);
    setLoadingBrain(true);
    try {
      const info = await atLeast(uploadBrain(file), MIN_LOADING_MS);
      await scoreNewBrain(info.id);
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
  const sentence = resultSentence(run);
  let finding = "Load a brain (.onnx or a .tar bundle) to begin.";
  if (loadingBrain) {
    finding = "Loading brain...";
  } else if (sentence !== null) {
    finding = sentence;
  } else if (running) {
    finding = "Running.";
  } else if (brain && batches.length > 0) {
    finding = `${batchSummary(batches[0])} on all levels. Press Start run to watch one.`;
  } else if (brain) {
    finding = "Ready. Press Start run.";
  }

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
              disabled={running || loadingBrain}
            />
          )}
          <FileButton accept={[".onnx", ".tar"]} onFiles={loadBrain}>Load brain</FileButton>
          {brain && <DownloadButton brainId={brain.id} />}
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
                hideLabel
                value={levelId}
                options={levelOptions(levels)}
                onChange={(id) => { setLevelId(id); dispatch({ type: "reset" }); }}
                disabled={running}
              />
            ) : undefined
          }
        >
          {levels === null ? (
            <p className="empty">Loading levels...</p>
          ) : (
            <MazeCanvas
              level={level}
              levels={levels}
              pos={run.pos}
              trail={run.trail}
              action={{
                label: runLedLabel(running),
                stop: running,
                enabled: running || (!!brain && !!level && !loadingBrain),
                onClick: running ? stop : start,
              }}
            />
          )}
        </Panel>

        <div className="right">
          <RatingPanel brain={brain} batch={batches[0] ?? null} working={batchWorking || loadingBrain} />
          <BatchPanel brain={brain} batches={batches} working={batchWorking} onRun={runAll} disabled={!brain || running || loadingBrain || batchWorking} />
        </div>
      </div>
      <RecipePanel brain={brain} />
    </div>
  );
}
