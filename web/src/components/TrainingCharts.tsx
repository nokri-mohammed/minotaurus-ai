import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import type { BrainMetrics } from "../protocol";
import { getBrainMetrics } from "../services";
import { type CurveRow, hasCurve, mergeCurves } from "../training";

type Panel = {
  title: string;
  keys: { key: keyof CurveRow; label: string; color: string }[];
  percent?: boolean; // the axis is a share from 0 to 1, shown as a percent
};

const PANELS: Panel[] = [
  {
    title: "Success rate",
    percent: true,
    keys: [
      { key: "success_rate", label: "Training", color: "var(--chart-1)" },
      { key: "validation_success", label: "Quiz", color: "var(--chart-2)" },
    ],
  },
  { title: "Average steps per try (lower is better)", keys: [{ key: "avg_steps", label: "Steps", color: "var(--chart-1)" }] },
  { title: "Average points per try", keys: [{ key: "avg_reward", label: "Points", color: "var(--chart-1)" }] },
  { title: "Random-move rate", percent: true, keys: [{ key: "epsilon", label: "Random moves", color: "var(--chart-1)" }] },
  { title: "Error (how far off the scores were)", keys: [{ key: "loss", label: "Error", color: "var(--chart-1)" }] },
];

function CurvePanel({ panel, rows, savedAt }: { panel: Panel; rows: CurveRow[]; savedAt: number | null }) {
  const config: ChartConfig = {};
  for (const k of panel.keys) config[k.key] = { label: k.label, color: k.color };
  const lines = [];
  for (const k of panel.keys) {
    if (!hasCurve(rows, k.key)) continue;
    lines.push(
      <Line
        key={k.key}
        dataKey={k.key}
        type="monotone"
        stroke={`var(--color-${k.key})`}
        strokeWidth={2}
        dot={k.key === "validation_success"}
        connectNulls
        isAnimationActive={false}
      />,
    );
  }
  if (lines.length === 0) return null;
  const showSaved = panel.percent === true && savedAt !== null;
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium">{panel.title}</p>
      <ChartContainer config={config} className="aspect-auto h-40 w-full">
        <LineChart data={rows} margin={{ left: 4, right: 12, top: 4 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="episode" tickLine={false} axisLine={false} tickMargin={6} minTickGap={32} />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={panel.percent ? 40 : 52}
            domain={panel.percent ? [0, 1] : ["auto", "auto"]}
            tickFormatter={panel.percent ? (v: number) => `${Math.round(v * 100)}%` : undefined}
          />
          <ChartTooltip content={<ChartTooltipContent labelFormatter={(_, items) => `Try ${items[0]?.payload?.episode ?? ""}`} />} />
          {showSaved && <ReferenceLine x={savedAt} stroke="var(--muted-foreground)" strokeDasharray="4 4" />}
          {lines}
        </LineChart>
      </ChartContainer>
    </div>
  );
}

/** The brain's training curves, drawn from its bundle's metrics with shadcn charts. */
export function TrainingCharts({ brainId }: { brainId: string }) {
  const [metrics, setMetrics] = useState<BrainMetrics | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setMetrics(null);
    setProblem(null);
    async function load() {
      try {
        const loaded = await getBrainMetrics(brainId);
        if (current) setMetrics(loaded);
      } catch (e) {
        if (current) setProblem(e instanceof Error ? e.message : "Could not read the training data.");
      }
    }
    void load();
    return () => {
      current = false;
    };
  }, [brainId]);

  const rows = useMemo(() => (metrics ? mergeCurves(metrics) : []), [metrics]);

  if (problem) return <p role="alert" className="problem">{problem}</p>;
  if (!metrics) return <p className="empty">Loading training data...</p>;
  if (rows.length === 0) return <p className="empty">This brain has no training data.</p>;
  const panels = [];
  for (const panel of PANELS) {
    panels.push(<CurvePanel key={panel.title} panel={panel} rows={rows} savedAt={metrics.saved_at ?? null} />);
  }
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">{panels}</div>
      {metrics.saved_at !== undefined && (
        <p className="muted">The dashed line marks try {metrics.saved_at}, the version that was saved.</p>
      )}
    </div>
  );
}
