import { expect, test } from "bun:test";
import { brainDownloadUrl } from "./endpoints/brains";

test("the download address is the brain's own download endpoint", () => {
  expect(brainDownloadUrl("ab12")).toBe("/api/brains/ab12/download");
});
