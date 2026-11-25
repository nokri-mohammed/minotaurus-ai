import { expect, test } from "bun:test";
import { authorView, verifyView } from "./verify";

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

test("an unsigned recipe says so; a signed one shows the author id and the first-seen day", () => {
  expect(authorView({}).label).toBe("Unsigned");
  expect(authorView({ signed_by: null }).tone).toBe("secondary");
  const signed = authorView({ signed_by: "9f3a1c0b7e2d4a58", author_first_seen: "2026-11-25T10:00:00+00:00" });
  expect(signed.label).toBe("Signed");
  expect(signed.detail).toContain("9f3a1c0b7e2d4a58");
  expect(signed.detail).toContain("first seen");
  expect(authorView({ signed_by: "9f3a1c0b7e2d4a58" }).detail).toBe("Author id 9f3a1c0b7e2d4a58.");
});
