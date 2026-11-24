import { useEffect, useState } from "react";
import { Arena } from "./Arena";
import { Brains } from "./Brains";
import { History } from "./History";
import { AppShell } from "./components";
import { type Page, pageFromHash } from "./page";
import type { BrainInfo } from "./protocol";
import { getAttempts, getBrains, importAttempts } from "./services";
import { type Attempt, loadLocalAttempts, markMigrated, migrationDone } from "./services/history";

export function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash));
  // One list of attempts for both pages; the Arena stays mounted (hidden) so a run goes on while you read History.
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  // The brains the server has loaded, newest first, and the one the Arena works with.
  const [brains, setBrains] = useState<BrainInfo[]>([]);
  const [brainId, setBrainId] = useState<string | null>(null);

  useEffect(() => {
    const onHashChange = () => setPage(pageFromHash(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    async function loadFromServer() {
      try {
        const known = await getBrains();
        setBrains(known);
        setBrainId(known[0]?.id ?? null);
        // Attempts saved in this browser by an older page go to the server once.
        const local = loadLocalAttempts();
        if (local.length > 0 && !migrationDone()) {
          await importAttempts(local);
          markMigrated();
        }
        setAttempts(await getAttempts());
      } catch {
        // the Arena shows "cannot reach the arena" when it cannot load the levels
      }
    }
    void loadFromServer();
  }, []);

  return (
    <AppShell page={page}>
      <Arena
        attempts={attempts}
        onAttempts={setAttempts}
        brains={brains}
        onBrains={setBrains}
        brainId={brainId}
        onBrainId={setBrainId}
        hidden={page !== "arena"}
      />
      <Brains brains={brains} hidden={page !== "brains"} />
      <History attempts={attempts} brains={brains} hidden={page !== "history"} />
    </AppShell>
  );
}
