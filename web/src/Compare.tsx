import { useEffect, useState } from "react";
import { brainLabel, brainOptions } from "./brainOptions";
import { compareRecipes } from "./brainsView";
import { type Col, DataTable, Panel, Select } from "./components";
import type { BrainInfo, BrainRecipe } from "./protocol";
import { getBrainRecipe } from "./services";

type Props = { brains: BrainInfo[]; hidden: boolean };

const NONE = "none";

function brainOf(brains: BrainInfo[], id: string): BrainInfo {
  return brains.find((b) => b.id === id) ?? { id, name: "?", method: "dqn", has_recipe: false, added_at: "" };
}

type CompareRow = { label: string; a: string; b: string };

function CompareTable({ title, rows, a, b, empty }: { title: string; rows: CompareRow[]; a: string; b: string; empty: string }) {
  const columns: Col<CompareRow>[] = [
    { id: "label", header: title, primary: true, render: (r) => r.label },
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
            <CompareTable title="Results" rows={comparison.results} a={nameA} b={nameB} empty="No results." />
          </>
        )}
      </Panel>
    </div>
  );
}
