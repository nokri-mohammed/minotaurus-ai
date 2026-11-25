import { expect, test } from "bun:test";
import { mergeCurves } from "./training";

test("points and quiz checks are merged by try number, in order", () => {
  const rows = mergeCurves({
    points: [
      { episode: 20, success_rate: 0.2, avg_steps: 40 },
      { episode: 10, success_rate: 0.1, avg_steps: 50, loss: 0.5 },
    ],
    quiz: [{ episode: 20, validation_success: 0.3 }, { episode: 15, validation_success: 0.25 }],
  });
  expect(rows.map((r) => r.episode)).toEqual([10, 15, 20]);
  expect(rows[0]).toEqual({ episode: 10, success_rate: 0.1, avg_steps: 50, loss: 0.5 });
  expect(rows[1]).toEqual({ episode: 15, validation_success: 0.25 });
  expect(rows[2]).toEqual({ episode: 20, success_rate: 0.2, avg_steps: 40, validation_success: 0.3 });
});

test("which curves exist: a curve the run never recorded is not drawn", () => {
  const rows = mergeCurves({ points: [{ episode: 10, success_rate: 0.1 }], quiz: [] });
  expect(rows).toEqual([{ episode: 10, success_rate: 0.1 }]);
});
