import { batchSummary, groupCount } from "../batch";
import type { BatchResult, BrainInfo } from "../protocol";
import { shortId } from "../brainOptions";
import { Button } from "./Button";
import { type Col, DataTable } from "./DataTable";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

const LEVEL_COLUMNS: Col<BatchResult["results"][number]>[] = [
  { id: "level", header: "Level", primary: true, render: (r) => r.name },
  { id: "group", header: "Group", secondary: true, render: (r) => (r.group === "test" ? "Test maze" : "Hand-made") },
  { id: "result", header: "Result", render: (r) => <StatusPill status={r.status} /> },
  { id: "steps", header: "Steps", align: "right", render: (r) => r.steps },
  { id: "time", header: "Time", align: "right", render: (r) => (r.status === "finished" ? `${r.seconds.toFixed(1)} s` : "–") },
];

type Props = { brain: BrainInfo | null; batches: BatchResult[]; working: boolean; onRun: () => void; disabled: boolean };

/** The result of the latest "run all levels" of the selected brain. */
export function BatchPanel({ brain, batches, working, onRun, disabled }: Props) {
  const latest = batches[0] ?? null;
  const note = working
    ? "Running every level..."
    : latest
      ? `${batchSummary(latest)}, ${when(latest.date)}`
      : brain
        ? `Press Run all levels to try ${brain.name} (${shortId(brain.id)}) on every portal level.`
        : "Load a brain first.";
  return (
    <Panel
      title="All levels"
      note={note}
      actions={<Button onClick={onRun} disabled={disabled}>{working ? "Running all..." : "Run all levels"}</Button>}
    >
      {latest && (
        <>
          <p className="finding">
            Hand-made {groupCount(latest, "hand-made").finished} of {groupCount(latest, "hand-made").total},
            test mazes {groupCount(latest, "test").finished} of {groupCount(latest, "test").total}
          </p>
          <div className="scroll">
            <DataTable label="All levels" columns={LEVEL_COLUMNS} rows={latest.results} rowId={(r) => r.level_id} empty="No levels." />
          </div>
        </>
      )}
    </Panel>
  );
}
