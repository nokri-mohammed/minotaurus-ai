import { useMemo } from "react";
import { Button, DataTable, Panel } from "./components";
import { attemptColumns, secs } from "./components/attemptColumns";
import { downloadAllLogs } from "./services/attemptLog";
import { type Attempt, summarize } from "./services/history";

type Props = { attempts: Attempt[]; hidden: boolean };

const COLUMNS = attemptColumns(true);

/** Every saved attempt, with a log download on each row and one for all of them. */
export function History({ attempts, hidden }: Props) {
  const summary = useMemo(() => summarize(attempts), [attempts]);
  let withLog = 0;
  for (const attempt of attempts) {
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
          <Button onPress={() => downloadAllLogs(attempts)} isDisabled={withLog === 0}>
            {`Download all logs (${withLog})`}
          </Button>
        </div>
      </header>
      <Panel title="All attempts" note="Saved in this browser. The log of the newest 100 attempts can be downloaded.">
        <DataTable label="All attempts" columns={COLUMNS} rows={attempts} rowId={(a) => a.id} empty="No attempts yet. Your runs are saved in this browser." />
      </Panel>
    </div>
  );
}
