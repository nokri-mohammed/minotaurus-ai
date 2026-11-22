import { describe, expect, test } from "bun:test";
import { wallLines } from "./draw";

describe("wallLines", () => {
  test("joins neighbouring wall cells with one thin line each", () => {
    const { segments } = wallLines(["#####", "#S.E#", "#####"]);
    // top row: 4 lines, bottom row: 4 lines, left and right columns: 2 lines each
    expect(segments.length).toBe(4 + 4 + 2 + 2);
    expect(segments).toContainEqual({ x1: 0, y1: 0, x2: 1, y2: 0 });
    expect(segments).toContainEqual({ x1: 0, y1: 0, x2: 0, y2: 1 });
  });

  test("an open cell breaks the line, so a gap in the outer wall stays a gap", () => {
    const { segments } = wallLines(["###", "#SE", "###"]);
    // right column: the wall cells (2,0) and (2,2) are not joined, because (2,1) is open
    expect(segments).not.toContainEqual({ x1: 2, y1: 0, x2: 2, y2: 1 });
    expect(segments).not.toContainEqual({ x1: 2, y1: 1, x2: 2, y2: 2 });
  });

  test("a wall cell with no wall neighbour is a lone post", () => {
    const { segments, posts } = wallLines(["...", ".#.", "..."]);
    expect(segments.length).toBe(0);
    expect(posts).toEqual([{ x: 1, y: 1 }]);
  });

  test("a wall cell that is part of a line is not also a post", () => {
    const { posts } = wallLines(["##"]);
    expect(posts.length).toBe(0);
  });
});
