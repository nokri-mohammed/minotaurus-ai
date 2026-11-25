// The colour theme: the person picks System, Light or Dark; "system" follows the device.
export type ThemeChoice = "system" | "light" | "dark";
export type Theme = "light" | "dark";

export const THEME_CHOICES: { id: ThemeChoice; label: string }[] = [
  { id: "system", label: "System" },
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
];

export function isThemeChoice(value: unknown): value is ThemeChoice {
  return value === "system" || value === "light" || value === "dark";
}

/** The theme to draw: the choice, or the device's setting when the choice is "system". */
export function resolveTheme(choice: ThemeChoice, systemIsDark: boolean): Theme {
  if (choice === "light") return "light";
  if (choice === "dark") return "dark";
  if (systemIsDark) return "dark";
  return "light";
}
