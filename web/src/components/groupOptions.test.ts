import { expect, test } from "bun:test";
import { groupOptions } from "./groupOptions";

test("options without a group stay in one section with no title", () => {
  const sections = groupOptions([{ id: "a", label: "A" }, { id: "b", label: "B" }]);
  expect(sections).toEqual([{ title: null, items: [{ id: "a", label: "A" }, { id: "b", label: "B" }] }]);
});

test("options are grouped by title, in the order each group first appears", () => {
  const sections = groupOptions([
    { id: "a", label: "A", group: "Hand-made levels" },
    { id: "b", label: "B", group: "Hand-made levels" },
    { id: "c", label: "C", group: "Test mazes" },
  ]);
  expect(sections.map((s) => s.title)).toEqual(["Hand-made levels", "Test mazes"]);
  expect(sections[0].items.map((o) => o.id)).toEqual(["a", "b"]);
  expect(sections[1].items.map((o) => o.id)).toEqual(["c"]);
});

test("an empty list gives no sections", () => {
  expect(groupOptions([])).toEqual([]);
});
