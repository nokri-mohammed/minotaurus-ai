import { useEffect, useState } from "react";
import { Arena } from "./Arena";
import { History } from "./History";
import { AppShell } from "./components";
import { type Page, pageFromHash } from "./page";
import { type Attempt, loadAttempts } from "./services/history";

export function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash));
  // One list for both pages; the Arena stays mounted (hidden) so a run goes on while you read History.
  const [attempts, setAttempts] = useState<Attempt[]>(() => loadAttempts());

  useEffect(() => {
    const onHashChange = () => setPage(pageFromHash(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <AppShell page={page}>
      <Arena attempts={attempts} onAttempts={setAttempts} hidden={page !== "arena"} />
      <History attempts={attempts} hidden={page !== "history"} />
    </AppShell>
  );
}
