import { describe, expect, test } from "bun:test";

import { ICON_SIZE, iconFor } from "./themeIcons";

describe("iconFor", () => {
  test("every picture is 9 x 9 and has lit dots", () => {
    for (const choice of ["system", "light", "dark"] as const) {
      const rows = iconFor(choice);
      expect(rows.length).toBe(ICON_SIZE);
      for (const row of rows) {
        expect(row.length).toBe(ICON_SIZE);
      }
      expect(rows.join("").includes("#")).toBe(true);
    }
  });
  test("the moon is a crescent: its upper right corner is dark", () => {
    expect(iconFor("dark")[0][8]).toBe(".");
  });
});
