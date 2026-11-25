// What the Random maze controls offer. The server ties difficulty to size (easy up to 9, medium up
// to 17, hard above), so a difficulty only limits which sizes can be picked. Sizes are odd.
export type MazeDifficulty = "easy" | "medium" | "hard";

export const MAZE_DIFFICULTIES: MazeDifficulty[] = ["easy", "medium", "hard"];

const RANGES: Record<MazeDifficulty, { from: number; to: number }> = {
  easy: { from: 5, to: 9 },
  medium: { from: 11, to: 17 },
  hard: { from: 19, to: 41 },
};

/** The odd sizes of one difficulty, smallest first. Example: easy gives 5, 7, 9. */
export function sizesFor(difficulty: MazeDifficulty): number[] {
  const range = RANGES[difficulty];
  const sizes: number[] = [];
  for (let size = range.from; size <= range.to; size += 2) sizes.push(size);
  return sizes;
}

/** The size a difficulty starts on: its middle size. */
export function defaultSizeFor(difficulty: MazeDifficulty): number {
  const sizes = sizesFor(difficulty);
  return sizes[Math.floor(sizes.length / 2)];
}

/** The difficulty a size belongs to. */
export function difficultyOf(size: number): MazeDifficulty {
  if (size <= RANGES.easy.to) return "easy";
  if (size <= RANGES.medium.to) return "medium";
  return "hard";
}

/** A seed typed by hand: digits only, 0 to 999999. Empty means "draw one". Null means not valid. */
export function parseSeed(text: string): number | undefined | null {
  const trimmed = text.trim();
  if (trimmed === "") return undefined;
  if (!/^\d{1,6}$/.test(trimmed)) return null;
  return Number(trimmed);
}
