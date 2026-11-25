import { describe, expect, test } from "bun:test";

import { FONT_HEIGHT, textLeds } from "./ledFont";

describe("textLeds", () => {
  test("is five LEDs high, with one blank column between letters", () => {
    const rows = textLeds("AB");
    expect(rows.length).toBe(FONT_HEIGHT);
    expect(rows[0].length).toBe(3 + 1 + 3);
  });
  test("an unknown character is a blank", () => {
    expect(textLeds("?")[0].every((n) => n === 0)).toBe(true);
  });
  test("lower case reads as upper case", () => {
    expect(textLeds("e")).toEqual(textLeds("E"));
  });
});
