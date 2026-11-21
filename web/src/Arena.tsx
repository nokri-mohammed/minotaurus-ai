import { useEffect, useReducer, useRef, useState } from "react";
import {
  Button, Cell, Column, FileTrigger, Label, ListBox, ListBoxItem, Popover, Row, Select,
  SelectValue, Table, TableBody, TableHeader,
} from "react-aria-components";
import { canvasSize, drawArena } from "./draw";
import { type Attempt, addAttempt, loadAttempts } from "./history";
import { type Api, type RunHandle } from "./net";
import type { BrainInfo, LevelInfo, RunMessage } from "./protocol";
import { idleRun, reduceRun } from "./run";

const RESULT_TEXT = { finished: "Finished", timed_out: "Timed out", error: "Error" } as const;

export function Arena({ api }: { api: Api }) {
  const [levels, setLevels] = useState<LevelInfo[]>([]);
  const [levelId, setLevelId] = useState<string | null>(null);
  const [brain, setBrain] = useState<BrainInfo | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [attempts, setAttempts] = useState<Attempt[]>(() => loadAttempts());
  const [run, dispatch] = useReducer(reduceRun, idleRun);
  const handle = useRef<RunHandle | null>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const saved = useRef(false);

  const level = levels.find((l) => l.id === levelId) ?? null;

  useEffect(() => {
    api.levels().then(
      (list) => {
        setLevels(list);
        setLevelId(list[0]?.id ?? null);
      },
      () => setProblem("Cannot reach the server. Start it with: uv run minotaurus dev"),
    );
    return () => handle.current?.close();
  }, [api]);

  useEffect(() => {
    const ctx = canvas.current?.getContext("2d");
    if (ctx && level) drawArena(ctx, level, run.pos, run.trail);
  }, [level, run.pos, run.trail]);

  // Save each finished run once.
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
    const onMessage = (m: RunMessage) => dispatch(m);
    handle.current = api.run(level.id, onMessage);
  }

  const running = run.phase === "running";
  const size = level ? canvasSize(level) : { width: 0, height: 0 };

  return (
    <>
      <section className="controls">
        <FileTrigger acceptedFileTypes={[".onnx"]} onSelect={loadBrain}>
          <Button>Load brain (.onnx)</Button>
        </FileTrigger>
        <span>{brain ? `${brain.name} (${brain.method})` : "No brain loaded"}</span>
        <Select selectedKey={levelId} onSelectionChange={(k) => { setLevelId(String(k)); dispatch({ type: "reset" }); }} isDisabled={running}>
          <Label>Level</Label>
          <Button><SelectValue /><span aria-hidden="true"> ▾</span></Button>
          <Popover>
            <ListBox items={levels}>
              {(l) => <ListBoxItem id={l.id} textValue={l.name}>{l.name} ({l.difficulty})</ListBoxItem>}
            </ListBox>
          </Popover>
        </Select>
        <Button onPress={start} isDisabled={!brain || !level || running}>Start run</Button>
      </section>

      {problem && <p role="alert" className="problem">{problem}</p>}

      <section className="arena">
        <canvas ref={canvas} width={size.width} height={size.height} aria-label="Maze with the dot" />
        <p role="status" className="readout">
          {run.phase === "idle" && "Load a brain, pick a level and press Start run."}
          {running && `Step ${run.steps} of ${run.stepLimit}, time ${run.seconds.toFixed(1)} s`}
          {run.phase === "done" && run.result &&
            (run.result.status === "finished"
              ? `Finished in ${run.result.steps} steps, ${run.result.seconds.toFixed(1)} s`
              : run.result.status === "timed_out"
                ? `Timed out after ${run.result.steps} steps (limit ${run.stepLimit})`
                : `Error: ${run.result.message ?? "the run failed"}`)}
        </p>
      </section>

      <section>
        <h2>Past attempts</h2>
        <Table aria-label="Past attempts">
          <TableHeader>
            <Column isRowHeader>Date</Column>
            <Column>Brain</Column>
            <Column>Method</Column>
            <Column>Level</Column>
            <Column>Result</Column>
            <Column>Steps</Column>
            <Column>Time</Column>
          </TableHeader>
          <TableBody items={attempts} renderEmptyState={() => "No attempts yet."}>
            {(a) => (
              <Row id={a.id}>
                <Cell>{new Date(a.date).toLocaleString()}</Cell>
                <Cell>{a.brain}</Cell>
                <Cell>{a.method}</Cell>
                <Cell>{a.level}</Cell>
                <Cell>{RESULT_TEXT[a.result]}</Cell>
                <Cell>{a.steps}</Cell>
                <Cell>{a.seconds.toFixed(1)} s</Cell>
              </Row>
            )}
          </TableBody>
        </Table>
      </section>
    </>
  );
}
