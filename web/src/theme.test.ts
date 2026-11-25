import { describe, expect, test } from "bun:test";

import { isThemeChoice, resolveTheme } from "./theme";

describe("resolveTheme", () => {
  test("system follows the device", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
  });
  test("light and dark ignore the device", () => {
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
  });
});

describe("isThemeChoice", () => {
  test("accepts the three choices only", () => {
    expect(isThemeChoice("system")).toBe(true);
    expect(isThemeChoice("blue")).toBe(false);
    expect(isThemeChoice(null)).toBe(false);
  });
});
