export type Page = "arena" | "history";

/** The page named by the address bar (`#history`). Anything else is the Arena. */
export function pageFromHash(hash: string): Page {
  if (hash === "#history") return "history";
  return "arena";
}
