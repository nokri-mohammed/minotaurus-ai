import { expect, test } from "bun:test";
import { defaultSizeFor, difficultyOf, parseSeed, sizesFor } from "./randomMaze";

test("each difficulty offers its odd sizes and no others", () => {
  expect(sizesFor("easy")).toEqual([5, 7, 9]);
  expect(sizesFor("medium")).toEqual([11, 13, 15, 17]);
  const hard = sizesFor("hard");
  expect(hard[0]).toBe(19);
  expect(hard[hard.length - 1]).toBe(41);
  for (const size of hard) expect(size % 2).toBe(1);
});

test("the difficulty of a size matches the server's rule", () => {
  expect(difficultyOf(9)).toBe("easy");
  expect(difficultyOf(11)).toBe("medium");
  expect(difficultyOf(17)).toBe("medium");
  expect(difficultyOf(19)).toBe("hard");
  for (const d of ["easy", "medium", "hard"] as const) {
    expect(difficultyOf(defaultSizeFor(d))).toBe(d);
  }
});

test("a typed seed is digits only; empty means draw one", () => {
  expect(parseSeed("")).toBeUndefined();
  expect(parseSeed(" 4821 ")).toBe(4821);
  expect(parseSeed("0")).toBe(0);
  expect(parseSeed("-1")).toBeNull();
  expect(parseSeed("12a")).toBeNull();
  expect(parseSeed("1000000")).toBeNull();
});
