import type { ReactNode } from "react";

type Props = { title: string; note?: ReactNode; actions?: ReactNode; className?: string; children: ReactNode };

/** A white card on the ground: a 16px title, an optional note, content below. */
export function Panel({ title, note, actions, className = "", children }: Props) {
  return (
    <section className={`panel ${className}`}>
      <header className="panel-head">
        <div>
          <h2>{title}</h2>
          {note && <p className="muted">{note}</p>}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}
