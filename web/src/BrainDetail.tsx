import { IconArrowLeft } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { BatchPanel, DownloadButton, RatingPanel, RecipePanel } from "./components";
import type { BatchResult, BrainInfo } from "./protocol";
import { getBatches, runAllLevels } from "./services";

type Props = { brain: BrainInfo | null; loading: boolean };

/** Everything about one brain: rating, the result on every level, how it was made, its file. */
export function BrainDetail({ brain, loading }: Props) {
  const [batches, setBatches] = useState<BatchResult[]>([]);
  const [working, setWorking] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const brainId = brain?.id ?? null;

  useEffect(() => {
    let current = true;
    setBatches([]);
    setProblem(null);
    async function load() {
      if (brainId === null) return;
      try {
        const list = await getBatches(brainId);
        if (current) setBatches(list);
      } catch (e) {
        if (current) setProblem(e instanceof Error ? e.message : "Could not read the results.");
      }
    }
    void load();
    return () => {
      current = false;
    };
  }, [brainId]);

  async function run() {
    if (brainId === null || working) return;
    setProblem(null);
    setWorking(true);
    try {
      const batch = await runAllLevels(brainId);
      setBatches([batch]);
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Could not run all levels.");
    } finally {
      setWorking(false);
    }
  }

  const back = (
    <a href="#brains" className="muted inline-flex items-center gap-1 hover:underline">
      <IconArrowLeft className="size-4" aria-hidden="true" />
      All brains
    </a>
  );

  if (!brain) {
    let text = "That brain is not loaded.";
    if (loading) text = "Loading...";
    return (
      <>
        {back}
        <p className="empty">{text}</p>
      </>
    );
  }
  return (
    <>
      <header className="title-row">
        <div className="flex flex-col gap-1">
          {back}
          <h1>{brain.name}</h1>
          <p className="finding">{brain.method} brain, loaded {brain.added_at.slice(0, 10)}, id {brain.id.slice(0, 8)}</p>
        </div>
        <div className="actions">
          <DownloadButton brainId={brain.id} />
        </div>
      </header>
      {problem && <p role="alert" className="problem">{problem}</p>}
      <div className="split">
        <RatingPanel brain={brain} batch={batches[0] ?? null} working={working} />
        <BatchPanel brain={brain} batches={batches} working={working} onRun={run} disabled={working} />
      </div>
      <RecipePanel brain={brain} />
    </>
  );
}
