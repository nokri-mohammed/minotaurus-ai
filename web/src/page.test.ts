import { expect, test } from "bun:test";
import { pageFromHash } from "./page";

test("the address bar picks the page, and Arena is the default", () => {
  expect(pageFromHash("#history")).toBe("arena"); // the History page is gone
  expect(pageFromHash("#brains")).toBe("brains");
  expect(pageFromHash("#arena")).toBe("arena");
  expect(pageFromHash("")).toBe("arena");
  expect(pageFromHash("#nope")).toBe("arena");
});
