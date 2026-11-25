// How the page words the result of re-checking a brain's scores.
import type { BrainRecipe, Verification } from "./protocol";

export type VerifyView = {
  label: string;
  tone: "positive" | "destructive" | "secondary";
  details: string[]; // one line for each claim that did not come out the same
};

function percentOrNumber(name: string, value: number): string {
  if (name === "validation" || name === "test") return `${Math.round(value * 100)}%`;
  return String(Math.round(value * 100) / 100);
}

export function verifyView(result: Verification): VerifyView {
  if (result.status === "verified") return { label: "Verified", tone: "positive", details: [] };
  if (result.status === "unavailable") return { label: "Not checked", tone: "secondary", details: [] };
  const details: string[] = [];
  for (const check of result.checks) {
    if (check.match) continue;
    const claimed = check.claimed === undefined ? "none" : percentOrNumber(check.name, check.claimed);
    const actual = check.actual === undefined ? "none" : percentOrNumber(check.name, check.actual);
    details.push(`${check.name}: the bundle says ${claimed}, the server got ${actual}`);
  }
  return { label: "Scores do not match", tone: "destructive", details };
}

export type AuthorView = { label: string; tone: "positive" | "secondary"; detail: string };

/** Who signed the bundle: the author id and when this server first saw it, or "Unsigned". */
export function authorView(recipe: Pick<BrainRecipe, "signed_by" | "author_first_seen">): AuthorView {
  if (!recipe.signed_by) {
    return { label: "Unsigned", tone: "secondary", detail: "Nobody vouches for who made this bundle." };
  }
  let detail = `Author id ${recipe.signed_by}.`;
  if (recipe.author_first_seen) {
    const day = new Date(recipe.author_first_seen).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
    detail = `Author id ${recipe.signed_by}, first seen here on ${day}.`;
  }
  return { label: "Signed", tone: "positive", detail };
}
