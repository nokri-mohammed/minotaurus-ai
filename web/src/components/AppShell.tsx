import type { ReactNode } from "react";

import type { Page } from "../page";

type Props = { page: Page; children: ReactNode };

/** Open plane: a labelled sidebar on the ground (a top bar on a phone) and a fluid canvas. */
export function AppShell({ page, children }: Props) {
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <img src="/icon.jpeg" alt="" width="28" height="28" />
          <span>minotaurus-ai</span>
        </div>
        <nav aria-label="Main">
          <a href="#arena" aria-current={page === "arena" ? "page" : undefined}>Arena</a>
          <a href="#brains" aria-current={page === "brains" ? "page" : undefined}>Brains</a>
          <a href="#history" aria-current={page === "history" ? "page" : undefined}>History</a>
        </nav>
        <p className="side-foot muted">Local arena, 127.0.0.1</p>
      </aside>
      <main className="canvas">{children}</main>
    </div>
  );
}
