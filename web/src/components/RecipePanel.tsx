import { useEffect, useState } from "react";
import type { BrainInfo, BrainRecipe } from "../protocol";
import { recipeSections } from "../recipe";
import { getBrainRecipe, verifyBrain } from "../services";
import type { Verification } from "../protocol";
import { verifyView } from "../verify";
import { Badge } from "@/components/ui/badge";
import { shortId } from "../brainOptions";
import { Button } from "./Button";
import { InfoTip } from "./InfoTip";
import { Panel } from "./Panel";
import { TrainingCharts } from "./TrainingCharts";

type Props = { brain: BrainInfo | null };

/** How the selected brain was made: its training settings and result, and the training graph. */
export function RecipePanel({ brain }: Props) {
  const [recipe, setRecipe] = useState<BrainRecipe | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [verifyProblem, setVerifyProblem] = useState<string | null>(null);

  const brainId = brain?.id ?? null;
  const hasRecipe = brain?.has_recipe ?? false;

  useEffect(() => {
    let current = true;
    setRecipe(null);
    setProblem(null);
    setCopied(false);
    setVerification(null);
    setVerifyProblem(null);
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

  // Ask the server to play the brain again and compare with the scores the bundle claims.
  useEffect(() => {
    let current = true;
    async function check() {
      if (brainId === null || !hasRecipe) return;
      try {
        const result = await verifyBrain(brainId);
        if (current) setVerification(result);
      } catch (e) {
        if (current) setVerifyProblem(e instanceof Error ? e.message : "Could not check the scores.");
      }
    }
    void check();
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
  const view = verification ? verifyView(verification) : null;
  return (
    <Panel
      title="Recipe"
      note={`${brain.name} (${shortId(brain.id)})`}
      actions={
        recipe ? (
          <div className="actions">
            <Button onClick={copyConfig}>{copied ? "Copied" : "Copy config"}</Button>
          </div>
        ) : undefined
      }
    >
      {problem && <p role="alert" className="problem">{problem}</p>}
      {!recipe && !problem && <p className="empty">Loading recipe...</p>}
      {recipe && (
        <div className="mb-4 flex flex-col gap-1">
          {verifyProblem && <p className="muted">Scores not checked: {verifyProblem}</p>}
          {!verification && !verifyProblem && <p className="muted">Checking the scores again on the server...</p>}
          {verification && view && (
            <>
              <div className="flex items-center gap-2">
                <Badge variant={view.tone}>{view.label}</Badge>
                <InfoTip label="Verified" />
                <span className="muted">{verification.message}</span>
              </div>
              {view.details.map((line) => (
                <p key={line} className="muted">{line}</p>
              ))}
              {verification.not_checked.length > 0 && (
                <p className="muted">Not repeated: {verification.not_checked.join(", ")} mazes (too many to replay).</p>
              )}
            </>
          )}
        </div>
      )}
      {recipe && recipe.has_graph && (
        <div className="mb-6">
          <h3 className="recipe-title mb-2 flex items-center gap-1">
            Training
            <InfoTip label="Training" />
          </h3>
          <TrainingCharts brainId={brain.id} />
        </div>
      )}
      {sections.map((section) => (
        <dl key={section.title} className="recipe">
          <dt className="recipe-title">{section.title}</dt>
          <dd>
            <dl className="recipe-rows">
              {section.rows.map((row) => (
                <div key={row.label} className="recipe-row">
                  <dt className="inline-flex items-center gap-1">
                    {row.label}
                    <InfoTip label={row.label} />
                  </dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </dd>
        </dl>
      ))}
    </Panel>
  );
}
