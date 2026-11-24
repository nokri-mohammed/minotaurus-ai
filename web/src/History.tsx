import { useMemo, useState } from "react";
import { Button, DataTable, Panel, Select } from "./components";
import { attemptColumns, secs } from "./components/attemptColumns";
import { brainLabel } from "./brainOptions";
import type { BrainInfo } from "./protocol";
import { downloadAllLogs } from "./services/attemptLog";
import { type Attempt, UNKNOWN_BRAIN, attemptsOf, summarize } from "./services/history";

type Props = { attempts: Attempt[]; brains: BrainInfo[]; hidden: boolean };

const COLUMNS = attemptColumns(true);
const ALL = "all";

/** Every saved attempt, for all brains or one, with a log download on each row and one for all of them. */
export function History({ attempts, brains, hidden }: Props) {
  const [filter, setFilter] = useState<string>(ALL);
  const shown = useMemo(() => (filter === ALL ? attempts : attemptsOf(attempts, filter)), [attempts, filter]);
  const summary = useMemo(() => summarize(shown), [shown]);

  // The brains that have attempts, named from the list of loaded brains or from the attempt itself.
  const options = useMemo(() => {
    const list = [{ id: ALL, label: "All brains" }];
    const seen = new Set<string>();
    for (const attempt of attempts) {
      if (seen.has(attempt.brainId)) continue;
      seen.add(attempt.brainId);
      const loaded = brains.find((b) => b.id === attempt.brainId);
      if (loaded) {
        list.push({ id: loaded.id, label: brainLabel(loaded) });
      } else if (attempt.brainId === UNKNOWN_BRAIN) {
        list.push({ id: UNKNOWN_BRAIN, label: "Unknown brain (older attempts)" });
      } else {
        list.push({ id: attempt.brainId, label: `${brainLabel({ id: attempt.brainId, name: attempt.brain })} (not loaded)` });
      }
    }
    return list;
  }, [attempts, brains]);

  let withLog = 0;
  for (const attempt of shown) {
    if (attempt.path) withLog += 1;
  }
  return (
    <div id="history" className="stack" hidden={hidden}>
      <header className="title-row">
        <div>
          <h1>History</h1>
          <p className="finding">
            {summary.total === 0
              ? "No attempts yet."
              : `${summary.total} attempts, ${summary.finished} finished, best ${summary.bestSeconds === null ? "–" : `${secs(summary.bestSeconds)} s`}`}
          </p>
        </div>
        <div className="actions">
          <Select label="Brain" value={filter} options={options} onChange={setFilter} />
          <Button onPress={() => downloadAllLogs(shown)} isDisabled={withLog === 0}>
            {`Download all logs (${withLog})`}
          </Button>
        </div>
      </header>
      <Panel title="All attempts" note="Saved on the server, in var/arena.db.">
        <DataTable label="All attempts" columns={COLUMNS} rows={shown} rowId={(a) => a.id} empty="No attempts yet." />
      </Panel>
    </div>
  );
}
