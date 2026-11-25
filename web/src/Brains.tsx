import { useEffect, useMemo, useState } from "react";
import { BrainDetail } from "./BrainDetail";
import { Panel, Select, Stars, TrendChart, type Col, DataTable } from "./components";
import { type BrainRow, brainRow, pileKey, pileLabel, trendPoints } from "./brainsView";
import type { BatchResult, BrainInfo, BrainRecipe } from "./protocol";
import { brainHash } from "./page";
import { getBatches, getBrainRecipe } from "./services";

type Props = { brains: BrainInfo[]; hidden: boolean; openId: string | null; loading: boolean };

type Detail = { brain: BrainInfo; recipe: BrainRecipe | null; batch: BatchResult | null };

const percent = (share: number | null) => (share === null ? "–" : `${Math.round(share * 100)}%`);

const COLUMNS: Col<BrainRow>[] = [
  { id: "name", header: "Brain", primary: true, render: (r) => `${r.name} (${r.id.slice(0, 8)})` },
  { id: "method", header: "Method", secondary: true, render: (r) => r.method },
  {
    id: "stars",
    header: "Stars",
    render: (r) => (r.stars === null ? "–" : <Stars count={r.stars} size="sm" />),
  },
  { id: "exam", header: "Exam", align: "right", render: (r) => percent(r.exam) },
  { id: "quiz", header: "Quiz", align: "right", secondary: true, render: (r) => percent(r.quiz) },
  { id: "portal", header: "Portal levels", align: "right", secondary: true, render: (r) => r.portal },
  { id: "runAll", header: "Run all levels", align: "right", render: (r) => r.runAll },
  { id: "pile", header: "Exam mazes", secondary: true, render: (r) => r.pile },
  { id: "network", header: "Network", secondary: true, render: (r) => r.network },
  { id: "lr", header: "Learning rate", align: "right", secondary: true, render: (r) => r.learningRate },
  { id: "added", header: "Added", secondary: true, render: (r) => r.added.slice(0, 10) },
];

/** Every loaded brain with its settings and scores, a compare of two, and the exam trend. */
export function Brains({ brains, hidden, openId, loading }: Props) {
  const [details, setDetails] = useState<Detail[]>([]);
  const [pile, setPile] = useState<string | null>(null);
  // Read each brain's recipe and its latest "run all levels" when the page is shown or the list changes.
  useEffect(() => {
    if (hidden || openId !== null) return;
    let current = true;
    async function load() {
      const loaded: Detail[] = [];
      for (const brain of brains) {
        let recipe: BrainRecipe | null = null;
        let batch: BatchResult | null = null;
        try {
          if (brain.has_recipe) recipe = await getBrainRecipe(brain.id);
          const batches = await getBatches(brain.id);
          batch = batches[0] ?? null;
        } catch {
          // a brain whose details cannot be read is still listed, with dashes
        }
        loaded.push({ brain, recipe, batch });
      }
      if (current) setDetails(loaded);
    }
    void load();
    return () => {
      current = false;
    };
  }, [brains, hidden, openId]);

  const rows = useMemo(() => {
    const list: BrainRow[] = [];
    for (const d of details) list.push(brainRow(d.brain, d.recipe, d.batch));
    return list;
  }, [details]);

  // The exam piles that exist, to pick which one the trend shows.
  const piles = useMemo(() => {
    const found = new Map<string, string>();
    for (const d of details) {
      if (!d.recipe) continue;
      const key = pileKey(d.recipe);
      if (key !== null && !found.has(key)) found.set(key, pileLabel(d.recipe));
    }
    return found;
  }, [details]);
  const activePile = pile !== null && piles.has(pile) ? pile : (piles.keys().next().value ?? null);
  const points = useMemo(() => (activePile === null ? [] : trendPoints(details, activePile)), [details, activePile]);

  let openBrain: BrainInfo | null = null;
  for (const brain of brains) {
    if (brain.id === openId) openBrain = brain;
  }

  const pileOptions: { id: string; label: string }[] = [];
  for (const [key, label] of piles) pileOptions.push({ id: key, label });

  if (openId !== null) {
    return (
      <div id="brains" className="stack" hidden={hidden}>
        <BrainDetail brain={openBrain} loading={loading} />
      </div>
    );
  }

  return (
    <div id="brains" className="stack" hidden={hidden}>
      <header className="title-row">
        <div>
          <h1>Brains</h1>
          <p className="finding">
            {brains.length === 0 ? "No brains loaded yet. Load one in the Arena." : `${brains.length} brains loaded.`}
          </p>
        </div>
      </header>

      <Panel title="All brains" note="Click a brain to open all its details. Stars are the share of levels it finished. Exam is the honest score: compare brains only when their exam mazes are the same.">
        <div className="scroll">
          <DataTable label="All brains" columns={COLUMNS} rows={rows} rowId={(r) => r.id} empty="No brains loaded yet." onRowClick={(r) => { window.location.hash = brainHash(r.id); }} />
        </div>
      </Panel>

      <Panel title="Exam score over time" note="Each dot is one brain, oldest to newest.">
        {pileOptions.length > 1 && (
          <Select label="Exam mazes" value={activePile} options={pileOptions} onChange={setPile} />
        )}
        {activePile !== null && <p className="muted">Exam mazes: {piles.get(activePile)}</p>}
        <TrendChart points={points} />
      </Panel>

    </div>
  );
}
