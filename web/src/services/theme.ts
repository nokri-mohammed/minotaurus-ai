// Keeps the theme choice in the browser and puts the resolved theme on <html data-theme>.
import { isThemeChoice, resolveTheme, type ThemeChoice } from "../theme";

const KEY = "minotaurus.theme";

export function loadThemeChoice(): ThemeChoice {
  try {
    const saved = window.localStorage.getItem(KEY);
    if (isThemeChoice(saved)) return saved;
  } catch {
    // Storage can be blocked: use the default.
  }
  return "system";
}

export function saveThemeChoice(choice: ThemeChoice): void {
  try {
    window.localStorage.setItem(KEY, choice);
  } catch {
    // Not saved; the choice still applies until the page is closed.
  }
}

function systemIsDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function applyThemeChoice(choice: ThemeChoice): void {
  document.documentElement.dataset.theme = resolveTheme(choice, systemIsDark());
}

/** Calls `onChange` when the device switches between light and dark. Returns a stop function. */
export function watchSystemTheme(onChange: () => void): () => void {
  const query = window.matchMedia("(prefers-color-scheme: dark)");
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}
