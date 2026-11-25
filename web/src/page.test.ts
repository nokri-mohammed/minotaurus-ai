import { expect, test } from "bun:test";
import { brainHash, brainIdFromHash, pageFromHash } from "./page";

test("the address bar picks the page, and Arena is the default", () => {
  expect(pageFromHash("#history")).toBe("arena"); // the History page is gone
  expect(pageFromHash("#brains")).toBe("brains");
  expect(pageFromHash("#arena")).toBe("arena");
  expect(pageFromHash("")).toBe("arena");
  expect(pageFromHash("#nope")).toBe("arena");
});

test("a brain's details address is part of the Brains page and carries its id", () => {
  const id = "ab".repeat(32);
  expect(pageFromHash(brainHash(id))).toBe("brains");
  expect(brainIdFromHash(brainHash(id))).toBe(id);
  expect(brainIdFromHash("#brains")).toBeNull();
  expect(brainIdFromHash("#brains/not-an-id")).toBeNull();
  expect(brainIdFromHash("#arena")).toBeNull();
});
