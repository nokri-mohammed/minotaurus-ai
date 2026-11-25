import { useEffect, useState, type ReactNode } from "react";

import type { Page } from "../page";
import { applyThemeChoice, loadThemeChoice, saveThemeChoice, watchSystemTheme } from "../services/theme";
import { isThemeChoice, THEME_CHOICES, type ThemeChoice } from "../theme";
import { Select } from "./Select";

type Props = { page: Page; children: ReactNode };

/** Open plane: a labelled sidebar on the ground (a top bar on a phone) and a fluid canvas. */
export function AppShell({ page, children }: Props) {
  const [choice, setChoice] = useState<ThemeChoice>(loadThemeChoice);

  useEffect(() => {
    applyThemeChoice(choice);
    return watchSystemTheme(() => applyThemeChoice(choice));
  }, [choice]);

  function pick(id: string) {
    if (!isThemeChoice(id)) return;
    saveThemeChoice(id);
    setChoice(id);
  }

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
        <div className="side-foot">
          <Select label="Theme" options={THEME_CHOICES} value={choice} onChange={pick} />
          <p className="muted">Local arena, 127.0.0.1</p>
        </div>
      </aside>
      <main className="canvas">{children}</main>
    </div>
  );
}
