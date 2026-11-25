import { useEffect, useState } from "react";
import { Arena } from "./Arena";
import { Brains } from "./Brains";
import { Compare } from "./Compare";
import { RandomMazePage } from "./RandomMazePage";
import { AppShell } from "./components";
import { type Page, brainIdFromHash, pageFromHash } from "./page";
import type { BrainInfo } from "./protocol";
import { getBrains } from "./services";

export function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash));
  const [openId, setOpenId] = useState<string | null>(() => brainIdFromHash(window.location.hash));
  const [loaded, setLoaded] = useState(false);
  // The Arena stays mounted (hidden) so a run goes on while you read the Brains page.
  // The brains the server has loaded, newest first, and the one the Arena works with.
  const [brains, setBrains] = useState<BrainInfo[]>([]);
  const [brainId, setBrainId] = useState<string | null>(null);

  useEffect(() => {
    const onHashChange = () => {
      setPage(pageFromHash(window.location.hash));
      setOpenId(brainIdFromHash(window.location.hash));
    };
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
      } finally {
        setLoaded(true);
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
      <RandomMazePage brains={brains} brainId={brainId} onBrainId={setBrainId} hidden={page !== "random"} />
      <Compare brains={brains} hidden={page !== "compare"} />
      <Brains brains={brains} hidden={page !== "brains"} openId={openId} loading={!loaded} />
    </AppShell>
  );
}
