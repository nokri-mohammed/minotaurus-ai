import { useEffect, useState } from "react";
import { brainLabel, brainOptions } from "./brainOptions";
import { type FullRow, compareRecipes } from "./brainsView";
import { Badge } from "@/components/ui/badge";
import { type Col, DataTable, InfoTip, Panel, Select, TrainingCharts } from "./components";
import type { BrainInfo, BrainRecipe } from "./protocol";
import { getBrainRecipe } from "./services";

type Props = { brains: BrainInfo[]; hidden: boolean };

const NONE = "none";

function brainOf(brains: BrainInfo[], id: string): BrainInfo {
  return brains.find((b) => b.id === id) ?? { id, name: "?", method: "dqn", has_recipe: false, added_at: "" };
}

type CompareRow = { label: string; a: string; b: string };

/** "Learning: Learning rate" shows as "Learning rate" with its info tip, like the Recipe in the Arena. */
function LabelWithTip({ label }: { label: string }) {
  const at = label.indexOf(": ");
  let name = label;
  if (at >= 0) name = label.slice(at + 2);
  return (
    <span className="inline-flex items-center gap-1">
      <span className="muted">{at >= 0 ? `${label.slice(0, at)}:` : ""}</span>
      {name}
      <InfoTip label={name} />
    </span>
  );
}

function FullTable({ rows, a, b }: { rows: FullRow[]; a: string; b: string }) {
  const columns: Col<FullRow>[] = [
    { id: "label", header: "Setting", primary: true, render: (r) => <LabelWithTip label={r.label} /> },
    { id: "a", header: a, render: (r) => r.a },
    { id: "b", header: b, render: (r) => r.b },
    { id: "differs", header: "", render: (r) => (r.differs ? <Badge variant="warning">differs</Badge> : null) },
  ];
  return <DataTable label="All settings" columns={columns} rows={rows} rowId={(r) => r.label} empty="No settings." />;
}

function CompareTable({ title, rows, a, b, empty }: { title: string; rows: CompareRow[]; a: string; b: string; empty: string }) {
  const columns: Col<CompareRow>[] = [
    { id: "label", header: title, primary: true, render: (r) => <LabelWithTip label={r.label} /> },
    { id: "a", header: a, render: (r) => r.a },
    { id: "b", header: b, render: (r) => r.b },
  ];
  return <DataTable label={title} columns={columns} rows={rows} rowId={(r) => r.label} empty={empty} />;
}

/** Pick two brains and see the settings that differ and their results side by side. */
export function Compare({ brains, hidden }: Props) {
  const [idA, setIdA] = useState<string>(NONE);
  const [idB, setIdB] = useState<string>(NONE);
  const [recipes, setRecipes] = useState<Record<string, BrainRecipe>>({});
  const [problem, setProblem] = useState<string | null>(null);

  // Read a brain's recipe once, when it is picked.
  useEffect(() => {
    let current = true;
    async function load(id: string) {
      if (id === NONE || recipes[id]) return;
      try {
        const recipe = await getBrainRecipe(id);
        if (current) setRecipes((known) => ({ ...known, [id]: recipe }));
      } catch (e) {
        if (current) setProblem(e instanceof Error ? e.message : "Could not read the recipe.");
      }
    }
    setProblem(null);
    void load(idA);
    void load(idB);
    return () => {
      current = false;
    };
  }, [idA, idB]);

  const left = recipes[idA] ?? null;
  const right = recipes[idB] ?? null;
  const comparison = left && right ? compareRecipes(left, right) : null;
  const withRecipe = brains.filter((b) => b.has_recipe);
  const options = [{ id: NONE, label: "Pick a brain" }, ...brainOptions(withRecipe)];
  const nameA = brainLabel(brainOf(brains, idA));
  const nameB = brainLabel(brainOf(brains, idB));

  const sides = [];
  if (idA !== NONE) sides.push({ id: idA, name: nameA });
  if (idB !== NONE) sides.push({ id: idB, name: nameB });
  const trained = [];
  for (const side of sides) {
    if (brains.find((b) => b.id === side.id)?.has_recipe) trained.push(side);
  }

  const columns = [];
  for (const side of trained) {
    columns.push(
      <div key={side.id} className="flex min-w-0 flex-col gap-2">
        <h3 className="recipe-title">{side.name}</h3>
        <TrainingCharts brainId={side.id} narrow />
      </div>,
    );
  }

  return (
    <div id="compare" className="stack" hidden={hidden}>
      <header className="title-row">
        <div>
          <h1>Compare</h1>
          <p className="finding">Pick two brains. Only the settings that differ are listed.</p>
        </div>
      </header>
      <Panel title="Compare two brains" note="Brains that came as bundles can be compared.">
        <div className="actions">
          <Select label="Brain A" value={idA} options={options} onChange={setIdA} />
          <Select label="Brain B" value={idB} options={options} onChange={setIdB} />
        </div>
        {problem && <p role="alert" className="problem">{problem}</p>}
        {!comparison && <p className="empty">Pick two brains that came as bundles.</p>}
        {comparison && !comparison.samePile && (
          <p role="alert" className="problem">These brains were tested on different exam mazes, so their scores are not comparable.</p>
        )}
        {comparison && (
          <>
            <CompareTable title="Settings that differ" rows={comparison.settings} a={nameA} b={nameB} empty="No differences: the settings are the same." />
            <h3 className="recipe-title mt-4">All settings</h3>
            <p className="muted mb-2">Mazes, brain, learning, exploring, rewards and training of each brain.</p>
            <FullTable rows={comparison.all} a={nameA} b={nameB} />
            <CompareTable title="Results" rows={comparison.results} a={nameA} b={nameB} empty="No results." />
          </>
        )}
      </Panel>
      {trained.length > 0 && (
        <Panel title="Training" note="The training curves of each brain, side by side. Each chart has its own scale.">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {columns}
          </div>
        </Panel>
      )}
    </div>
  );
}
