import { countOutcomes, layoutLine, stepsOverTime } from "../chart";
import type { Attempt } from "../services/history";

type Props = { attempts: Attempt[] };

const BOX = { width: 360, height: 130, pad: 22 };

function StepsChart({ attempts }: Props) {
  const steps = stepsOverTime(attempts);
  if (steps.length === 0) {
    return <p className="empty">No finished run yet. Steps per run will be drawn here.</p>;
  }
  const points = layoutLine(steps, BOX);
  let max = 0;
  for (const value of steps) {
    if (value > max) max = value;
  }
  let line = "";
  for (const p of points) {
    line += `${p.x},${p.y} `;
  }
  const last = points[points.length - 1];
  const bottom = BOX.height - BOX.pad;
  return (
    <svg
      viewBox={`0 0 ${BOX.width} ${BOX.height}`}
      className="chart"
      role="img"
      aria-label={`Steps per finished run, oldest to newest: ${steps.join(", ")}`}
    >
      <line x1={BOX.pad} x2={BOX.width - BOX.pad} y1={bottom} y2={bottom} className="chart-rule" />
      <line x1={BOX.pad} x2={BOX.width - BOX.pad} y1={BOX.pad} y2={BOX.pad} className="chart-rule" />
      <text x={BOX.pad - 6} y={bottom + 4} className="chart-axis" textAnchor="end">0</text>
      <text x={BOX.pad - 6} y={BOX.pad + 4} className="chart-axis" textAnchor="end">{max}</text>
      <polyline points={line} className="chart-line" fill="none" />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} className="chart-dot" />
      ))}
      <text x={last.x} y={last.y - 8} className="chart-label" textAnchor="end">{steps[steps.length - 1]}</text>
    </svg>
  );
}

function OutcomeBars({ attempts }: Props) {
  const counts = countOutcomes(attempts);
  const rows = [
    { key: "finished", label: "Finished", count: counts.finished },
    { key: "timed_out", label: "Timed out", count: counts.timed_out },
    { key: "error", label: "Failed", count: counts.error },
  ];
  const total = attempts.length;
  return (
    <div className="bars">
      {rows.map((row) => (
        <div key={row.key} className="bar-row">
          <span className="bar-label">{row.label}</span>
          <span className="bar-track">
            <span className={`bar-fill bar-${row.key}`} style={{ width: total ? `${(100 * row.count) / total}%` : "0%" }} />
          </span>
          <span className="bar-count">{row.count}</span>
        </div>
      ))}
    </div>
  );
}

/** Two small charts from the attempts saved in this browser: steps per finished run (are you
 *  getting shorter?) and how the runs ended. */
export function AttemptsCharts({ attempts }: Props) {
  if (attempts.length === 0) {
    return <p className="empty">Run a brain to see your progress here.</p>;
  }
  return (
    <div className="charts">
      <div>
        <p className="muted chart-title">Steps per finished run (lower is better)</p>
        <StepsChart attempts={attempts} />
      </div>
      <div>
        <p className="muted chart-title">How runs ended</p>
        <OutcomeBars attempts={attempts} />
      </div>
    </div>
  );
}
