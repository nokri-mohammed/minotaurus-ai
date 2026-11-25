// How the page words the result of re-checking a brain's scores.
import type { Verification } from "./protocol";

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
