import { describe, expect, test } from "bun:test";
import type { LevelInfo } from "./protocol";
import { boardSizeFor, canvasSize, cellSizeFor, headerText, ledPattern, screenCells } from "./draw";

const level = (grid: string[]): LevelInfo => ({
  id: "t", name: "t", difficulty: "easy", group: "hand-made", grid, step_limit: 10,
});

// One letter per kind, so a row reads like the maze: # wall, E exit, S start, . path, @ dot, space floor.
const LETTERS = { wall: "#", floor: " ", trail: ".", dot: "@", exit: "E", start: "S" } as const;
const text = (rows: ReturnType<typeof screenCells>) => rows.map((r) => r.map((c) => LETTERS[c.kind]).join(""));

describe("screenCells", () => {
  test("walls, exit and start keep their squares and the dot starts on the start", () => {
    const rows = screenCells(level(["#####", "#S.E#", "#####"]), null, []);
    expect(text(rows)).toEqual(["#####", "#@ E#", "#####"]);
  });

  test("the dot is @ where it stands and the start shows S once it has left", () => {
    const rows = screenCells(level(["#####", "#S.E#", "#####"]), { x: 2, y: 1 }, []);
    expect(text(rows)[1]).toBe("#S@E#");
  });

  test("the walked path is dots, newer ones brighter", () => {
    const rows = screenCells(level(["#####", "#S..E#"]), { x: 3, y: 1 }, [{ x: 1, y: 1 }, { x: 2, y: 1 }]);
    expect(text(rows)[1]).toBe("#..@E#");
    expect(rows[1][2].fade).toBeGreaterThan(rows[1][1].fade);
  });

  test("the path never overwrites a wall or the exit", () => {
    const rows = screenCells(level(["#E"]), { x: 0, y: 0 }, [{ x: 0, y: 0 }, { x: 1, y: 0 }]);
    expect(rows[0][1].kind).toBe("exit");
  });

  test("only the last 40 squares of the path are shown", () => {
    const grid = ["#" + ".".repeat(60) + "#"];
    const trail = [];
    for (let x = 1; x <= 50; x += 1) trail.push({ x, y: 0 });
    const rows = screenCells(level(grid), { x: 51, y: 0 }, trail);
    expect(rows[0][1].kind).toBe("floor");
    expect(rows[0][50].kind).toBe("trail");
  });
});

describe("ledPattern", () => {
  const lit = (kind: Parameters<typeof ledPattern>[0]) => ledPattern(kind).flat().filter((n) => n === 1).length;

  test("the dot is made of 5 small LEDs, the exit flag of 6, a wall of 9, the path of 1", () => {
    expect(lit("dot")).toBe(5);
    expect(lit("exit")).toBe(6);
    expect(lit("wall")).toBe(9);
    expect(lit("trail")).toBe(1);
  });

  test("an empty square has no lit LED", () => {
    expect(lit("floor")).toBe(0);
    expect(lit("start")).toBe(0);
  });
});

describe("board", () => {
  test("the board is as big as the biggest level, so small mazes get the same LED size", () => {
    const big = level(["#".repeat(41), "#".repeat(41)]);
    const small = level(["#####", "#S.E#", "#####"]);
    expect(boardSizeFor([small, big])).toBe(41);
    expect(boardSizeFor([small])).toBe(5);
    expect(cellSizeFor(41, 410) * 41).toBeCloseTo(410, 5);
    expect(cellSizeFor(41, 560)).toBe(cellSizeFor(boardSizeFor([small, big]), 560));
  });
});

describe("title strip", () => {
  test("the text is the level name and its size", () => {
    const named = { ...level(["#####", "#S.E#", "#####"]), name: "easy-01" };
    expect(headerText(named)).toBe("easy-01 5x3");
  });
  test("the panel is taller than the board by six LED rows (5 of text, 1 blank)", () => {
    const size = canvasSize(10, 30);
    expect(size.height).toBe(300 + 60);
    expect(size.width).toBe(300);
  });
});
