import { useEffect, useState } from "react";
import { Arena } from "./Arena";
import { Brains } from "./Brains";
import { AppShell } from "./components";
import { type Page, pageFromHash } from "./page";
import type { BrainInfo } from "./protocol";
import { getBrains } from "./services";

export function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash));
  // The Arena stays mounted (hidden) so a run goes on while you read the Brains page.
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
      } catch {
        // the Arena shows "cannot reach the arena" when it cannot load the levels
      }
    }
    void loadFromServer();
  }, []);

  return (
    <AppShell page={page}>
      <Arena
        brains={brains}
        onBrains={setBrains}
        brainId={brainId}
        onBrainId={setBrainId}
        hidden={page !== "arena"}
      />
      <Brains brains={brains} hidden={page !== "brains"} />
    </AppShell>
  );
}
