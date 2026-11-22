import type { ReactNode } from "react";

type Props = { children: ReactNode };

/** Open plane: a labelled sidebar on the ground (a top bar on a phone) and a fluid canvas. */
export function AppShell({ children }: Props) {
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <img src="/icon.jpeg" alt="" width="28" height="28" />
          <span>minotaurus-ai</span>
        </div>
        <nav aria-label="Main">
          <a href="#arena" aria-current="page">Arena</a>
        </nav>
        <p className="side-foot muted">Local arena, 127.0.0.1</p>
      </aside>
      <main className="canvas">{children}</main>
    </div>
  );
}
