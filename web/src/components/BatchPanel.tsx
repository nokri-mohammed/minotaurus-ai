import { batchPercent, batchSummary, groupCount } from "../batch";
import type { BatchResult, BrainInfo } from "../protocol";
import { shortId } from "../brainOptions";
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
  { id: "route", header: "Route", align: "right", render: (r) => (r.path_ratio ? `${r.path_ratio.toFixed(2)}x` : "–") },
];

const EARLIER_COLUMNS: Col<BatchResult>[] = [
  { id: "date", header: "Date", primary: true, render: (b) => when(b.date) },
  { id: "done", header: "Finished", render: (b) => batchSummary(b) },
];

type Props = { brain: BrainInfo | null; batches: BatchResult[]; working: boolean };

/** The result of the latest "run all levels" of the selected brain, and the earlier ones to compare. */
export function BatchPanel({ brain, batches, working }: Props) {
  const latest = batches[0] ?? null;
  const note = working
    ? "Running every level..."
    : latest
      ? `${batchSummary(latest)}, ${when(latest.date)}`
      : brain
        ? `Press Run all levels to try ${brain.name} (${shortId(brain.id)}) on every portal level.`
        : "Load a brain first.";
  return (
    <Panel title="All levels" note={note}>
      {latest && (
        <>
          <p className="finding">
            Hand-made {groupCount(latest, "hand-made").finished} of {groupCount(latest, "hand-made").total},
            test mazes {groupCount(latest, "test").finished} of {groupCount(latest, "test").total}
            {batches.length > 1 && `. Last time: ${batchPercent(batches[1])}%.`}
          </p>
          <div className="scroll">
            <DataTable label="All levels" columns={LEVEL_COLUMNS} rows={latest.results} rowId={(r) => r.level_id} empty="No levels." />
          </div>
          {batches.length > 1 && (
            <>
              <h3 className="recipe-title">Earlier runs of this brain</h3>
              <DataTable label="Earlier runs" columns={EARLIER_COLUMNS} rows={batches.slice(1)} rowId={(b) => b.id} empty="None." />
            </>
          )}
        </>
      )}
    </Panel>
  );
}
