import { expect, test } from "bun:test";
import { verifyView } from "./verify";

test("a verified bundle gets a green label and no details", () => {
  expect(verifyView({ status: "verified", message: "ok", checks: [], not_checked: ["train"] })).toEqual({
    label: "Verified", tone: "positive", details: [],
  });
});

test("an unavailable check is neutral", () => {
  expect(verifyView({ status: "unavailable", message: "x", checks: [], not_checked: [] }).tone).toBe("secondary");
});

test("a mismatch lists only the claims that differ, with both numbers", () => {
  const view = verifyView({
    status: "mismatch",
    message: "x",
    checks: [
      { name: "validation", claimed: 0.5, actual: 0.5, match: true },
      { name: "test", claimed: 1, actual: 0.68, match: false },
    ],
    not_checked: ["train"],
  });
  expect(view.label).toBe("Scores do not match");
  expect(view.tone).toBe("destructive");
  expect(view.details).toEqual(["test: the bundle says 100%, the server got 68%"]);
});
