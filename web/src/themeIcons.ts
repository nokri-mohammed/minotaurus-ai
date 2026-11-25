// 9 x 9 dot-matrix pictures for the theme switch: "#" is a lit dot.
import type { ThemeChoice } from "./theme";

export const ICON_SIZE = 9;

const SUN = [
  "....#....",
  ".#.....#.",
  "..#...#..",
  "...###...",
  "#..###..#",
  "...###...",
  "..#...#..",
  ".#.....#.",
  "....#....",
];

const MONITOR = [
  ".........",
  ".#######.",
  ".#.....#.",
  ".#.....#.",
  ".#.....#.",
  ".#######.",
  "....#....",
  "...###...",
  ".........",
];

/** A crescent: a disc with a second disc cut out of its upper right. */
function moonRows(): string[] {
  const rows: string[] = [];
  for (let y = 0; y < ICON_SIZE; y += 1) {
    let row = "";
    for (let x = 0; x < ICON_SIZE; x += 1) {
      const inOuter = (x - 4) ** 2 + (y - 4) ** 2 <= 4.3 ** 2;
      const inCut = (x - 6.2) ** 2 + (y - 2.8) ** 2 <= 3.6 ** 2;
      if (inOuter && !inCut) {
        row += "#";
      } else {
        row += ".";
      }
    }
    rows.push(row);
  }
  return rows;
}

export function iconFor(choice: ThemeChoice): string[] {
  if (choice === "dark") return moonRows();
  if (choice === "light") return SUN;
  return MONITOR;
}
