import { expect, test } from "bun:test";
import { runLedLabel } from "./runButton";

test("the run button says START while idle and STOP while a run goes", () => {
  expect(runLedLabel(false)).toBe("> START");
  expect(runLedLabel(true)).toBe("# STOP");
});
