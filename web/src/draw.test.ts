import { describe, expect, test } from "bun:test";
import type { LevelInfo } from "./protocol";
import { screenCells } from "./draw";

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
