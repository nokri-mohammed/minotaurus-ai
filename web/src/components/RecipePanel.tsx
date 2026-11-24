import { useEffect, useState } from "react";
import type { BrainInfo, BrainRecipe } from "../protocol";
import { recipeSections } from "../recipe";
import { brainGraphUrl, getBrainRecipe } from "../services";
import { shortId } from "../brainOptions";
import { Button } from "./Button";
import { Panel } from "./Panel";

type Props = { brain: BrainInfo | null };

/** How the selected brain was made: its training settings and result, and the training graph. */
export function RecipePanel({ brain }: Props) {
  const [recipe, setRecipe] = useState<BrainRecipe | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showGraph, setShowGraph] = useState(false);

  const brainId = brain?.id ?? null;
  const hasRecipe = brain?.has_recipe ?? false;

  useEffect(() => {
    let current = true;
    setRecipe(null);
    setProblem(null);
    setCopied(false);
    setShowGraph(false);
    async function load() {
      if (brainId === null || !hasRecipe) return;
      try {
        const loaded = await getBrainRecipe(brainId);
        if (current) setRecipe(loaded);
      } catch (e) {
        if (current) setProblem(e instanceof Error ? e.message : "Could not read the recipe.");
      }
    }
    void load();
    return () => {
      current = false;
    };
  }, [brainId, hasRecipe]);

  async function copyConfig() {
    if (!recipe) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(recipe.config, null, 2));
      setCopied(true);
    } catch {
      setProblem("Could not copy. Select the settings by hand instead.");
    }
  }

  if (!brain) {
    return <Panel title="Recipe" note="Load a brain to see how it was made."><p className="empty">No brain loaded.</p></Panel>;
  }
  if (!brain.has_recipe) {
    return (
      <Panel title="Recipe" note={`${brain.name} (${shortId(brain.id)})`}>
        <p className="empty">
          This brain came as a plain .onnx file, so its training settings are not known. Pack its run folder
          with <code>uv run minotaurus pack &lt;run folder&gt;</code> and load the .tar instead.
        </p>
      </Panel>
    );
  }
  const sections = recipe ? recipeSections(recipe) : [];
  return (
    <Panel
      title="Recipe"
      note={`${brain.name} (${shortId(brain.id)})`}
      actions={
        recipe ? (
          <div className="actions">
            {recipe.has_graph && <Button onPress={() => setShowGraph(!showGraph)}>{showGraph ? "Hide graph" : "Training graph"}</Button>}
            <Button onPress={copyConfig}>{copied ? "Copied" : "Copy config"}</Button>
          </div>
        ) : undefined
      }
    >
      {problem && <p role="alert" className="problem">{problem}</p>}
      {!recipe && !problem && <p className="empty">Loading recipe...</p>}
      {sections.map((section) => (
        <dl key={section.title} className="recipe">
          <dt className="recipe-title">{section.title}</dt>
          <dd>
            <dl className="recipe-rows">
              {section.rows.map((row) => (
                <div key={row.label} className="recipe-row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </dd>
        </dl>
      ))}
      {recipe && showGraph && <img className="recipe-graph" src={brainGraphUrl(brain.id)} alt={`Training graph of ${brain.name}`} />}
    </Panel>
  );
}
