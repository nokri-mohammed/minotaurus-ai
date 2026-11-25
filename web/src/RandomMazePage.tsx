import { useEffect, useReducer, useRef, useState } from "react";
import { Confetti, MazeCanvas, Panel, RandomMazePanel, Select } from "./components";
import { brainOptions, shortId } from "./brainOptions";
import type { BrainInfo, LevelInfo, RandomMazeRequest } from "./protocol";
import { idleRun, reduceRun, resultSentence } from "./run";
import { runLedLabel } from "./runButton";
import { type RunHandle, generateMaze, openRun } from "./services";

type Props = {
  brains: BrainInfo[];
  brainId: string | null;
  onBrainId: (id: string | null) => void;
  hidden: boolean;
};

/**
 * Make a random maze (pick difficulty and size, press Generate) and watch the selected brain run it.
 * Nothing here is scored or saved: the Arena's "Run all levels" is the record.
 */
export function RandomMazePage({ brains, brainId, onBrainId, hidden }: Props) {
  const [level, setLevel] = useState<LevelInfo | null>(null);
  const [generating, setGenerating] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [run, dispatch] = useReducer(reduceRun, idleRun);
  const handle = useRef<RunHandle | null>(null);
  const [burst, setBurst] = useState(0);

  const brain = brains.find((b) => b.id === brainId) ?? null;
  const running = run.phase === "running";

  useEffect(() => {
    return () => handle.current?.close();
  }, []);

  useEffect(() => {
    if (run.phase === "done" && run.result?.status === "finished") setBurst((n) => n + 1);
  }, [run.phase, run.result]);

  async function generate(request: RandomMazeRequest) {
    if (generating || running) return;
    setProblem(null);
    setGenerating(true);
    try {
      const fresh = await generateMaze(request);
      setLevel(fresh);
      dispatch({ type: "reset" });
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Could not make a random maze.");
    } finally {
      setGenerating(false);
    }
  }

  function start() {
    if (!level || !brain) return;
    handle.current?.close();
    setProblem(null);
    handle.current = openRun(level.id, brain.id, dispatch);
  }

  function stop() {
    handle.current?.close();
    dispatch({ type: "stopped" });
  }

  const sentence = resultSentence(run);
  let finding = "Pick a difficulty and a size, then press Generate.";
  if (brains.length === 0) {
    finding = "Load a brain in the Arena first.";
  } else if (sentence !== null) {
    finding = sentence;
  } else if (running) {
    finding = "Running.";
  } else if (level) {
    finding = "Press Start run to watch the brain on this maze.";
  }

  return (
    <div id="random" className="stack" hidden={hidden}>
      <Confetti burst={burst} />
      <header className="title-row">
        <div>
          <h1>Random maze</h1>
          <p role="status" className="finding">{finding}</p>
        </div>
        <div className="actions">
          {brains.length > 0 && (
            <Select
              label="Brain"
              value={brainId}
              options={brainOptions(brains)}
              onChange={(id) => { onBrainId(id); dispatch({ type: "reset" }); }}
              disabled={running}
            />
          )}
        </div>
      </header>

      {problem && <p role="alert" className="problem">{problem}</p>}

      <div className="split">
        <RandomMazePanel working={generating} disabled={running} onGenerate={generate} />
        <Panel
          title={level ? level.name : "Maze"}
          note={brain ? `${brain.name} (${shortId(brain.id)})` : "No brain loaded"}
        >
          {level === null ? (
            <p className="empty">No maze yet. Press Generate.</p>
          ) : (
            <MazeCanvas
              level={level}
              levels={[level]}
              pos={run.pos}
              trail={run.trail}
              action={{
                label: runLedLabel(running),
                stop: running,
                enabled: running || !!brain,
                onClick: running ? stop : start,
              }}
            />
          )}
        </Panel>
      </div>
    </div>
  );
}
