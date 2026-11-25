export type Page = "arena" | "brains";

/** The page named by the address bar (`#history`). Anything else is the Arena. */
export function pageFromHash(hash: string): Page {
  if (hash === "#brains") return "brains";
  return "arena";
}
