export type Page = "arena" | "brains" | "compare";

/** The page named by the address bar. `#brains/<id>` is a brain's details, still the Brains page. */
export function pageFromHash(hash: string): Page {
  if (hash === "#compare") return "compare";
  if (hash === "#brains" || hash.startsWith("#brains/")) return "brains";
  return "arena";
}

/** The brain id in `#brains/<64 hex characters>`, or null for the list. */
export function brainIdFromHash(hash: string): string | null {
  const match = /^#brains\/([0-9a-f]{64})$/.exec(hash);
  if (match === null) return null;
  return match[1];
}

/** The address of a brain's details page. */
export function brainHash(brainId: string): string {
  return `#brains/${brainId}`;
}
