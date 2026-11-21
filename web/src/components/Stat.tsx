type Props = { label: string; value: string; unit?: string; note?: string };

/** A figure set in type, not a tile: small grey label, 30px number, unit as a grey suffix. */
export function Stat({ label, value, unit, note }: Props) {
  return (
    <div className="stat">
      <p className="muted">{label}</p>
      <p className="stat-value">
        {value}
        {unit && <span className="stat-unit"> {unit}</span>}
      </p>
      {note && <p className="muted">{note}</p>}
    </div>
  );
}
