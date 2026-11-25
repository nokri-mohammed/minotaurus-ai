import type { Attempt } from "../services/history";
import { downloadAttemptLog } from "../services/attemptLog";
import { Button } from "./Button";
import type { Col } from "./DataTable";
import { StatusPill } from "./StatusPill";

const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
export const secs = (n: number) => n.toFixed(1);

/** The columns of an attempts table. With `withLog`, a last column has the Download button. */
export function attemptColumns(withLog: boolean): Col<Attempt>[] {
  const columns: Col<Attempt>[] = [
    { id: "date", header: "Date", primary: true, render: (a) => when(a.date) },
    { id: "brain", header: "Brain", render: (a) => a.brain },
    { id: "method", header: "Method", secondary: true, render: (a) => a.method },
    { id: "level", header: "Level", secondary: true, render: (a) => a.level },
    { id: "result", header: "Result", render: (a) => <StatusPill status={a.result} /> },
    { id: "steps", header: "Steps", align: "right", render: (a) => a.steps },
    { id: "time", header: "Time", align: "right", render: (a) => `${secs(a.seconds)} s` },
  ];
  if (withLog) {
    columns.push({
      id: "log",
      header: "Log",
      render: (a) => (a.path ? <Button onClick={() => downloadAttemptLog(a)}>Download</Button> : "–"),
    });
  }
  return columns;
}
