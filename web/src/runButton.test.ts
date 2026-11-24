import { expect, test } from "bun:test";
import { runButtonText } from "./runButton";

test("the button says play while idle and stop while a run goes", () => {
  expect(runButtonText(false)).toBe("▶ Start run");
  expect(runButtonText(true)).toBe("■ Stop");
});
