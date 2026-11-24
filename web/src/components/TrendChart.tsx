import type { TrendPoint } from "../brainsView";

const WIDTH = 600;
const HEIGHT = 180;
const PAD = 28;

/** The exam score of each brain, oldest to newest, so you can see whether new recipes get better. */
export function TrendChart({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) return <p className="empty">No brains with an exam score on this pile yet.</p>;
  const xOf = (index: number) => (points.length === 1 ? WIDTH / 2 : PAD + (index * (WIDTH - 2 * PAD)) / (points.length - 1));
  const yOf = (exam: number) => HEIGHT - PAD - exam * (HEIGHT - 2 * PAD);
  const line: string[] = [];
  points.forEach((point, index) => line.push(`${xOf(index)},${yOf(point.exam)}`));
  const guides = [0, 0.5, 1];
  return (
    <svg className="trend" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Exam score of each brain, oldest to newest">
      {guides.map((g) => (
        <g key={g}>
          <line x1={PAD} x2={WIDTH - PAD} y1={yOf(g)} y2={yOf(g)} className="trend-guide" />
          <text x={PAD - 6} y={yOf(g) + 4} textAnchor="end" className="trend-label">{`${g * 100}%`}</text>
        </g>
      ))}
      {points.length > 1 && <polyline points={line.join(" ")} className="trend-line" />}
      {points.map((point, index) => (
        <circle key={point.id} cx={xOf(index)} cy={yOf(point.exam)} r={5} className="trend-dot">
          <title>{`${point.name}: ${Math.round(point.exam * 100)}% on the exam`}</title>
        </circle>
      ))}
    </svg>
  );
}
