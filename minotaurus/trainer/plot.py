"""Draw a training graph from a run's metrics.jsonl."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

# Draw into a file, never open a window (training may run without a screen).
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def read_metrics(path: str | Path) -> list[dict]:
    """One dict per line of metrics.jsonl, in the order they were written."""
    rows = []
    for text in Path(path).read_text().splitlines():
        if text.strip():
            rows.append(json.loads(text))
    return rows


def _column(rows: list[dict], name: str) -> list:
    values = []
    for row in rows:
        values.append(row[name])
    return values


def plot_metrics(metrics_path: str | Path, out_path: str | Path, title: str = "") -> Path:
    """Save a PNG with the learning curves. Returns the path of the PNG.

    Panels: success rate, average steps, average points, random-move rate, and the error when the
    run recorded one.
    """
    rows = []
    for row in read_metrics(metrics_path):
        if "avg_steps" in row:  # training lines only; validation lines (G4) are skipped
            rows.append(row)
    episodes = _column(rows, "episode")

    panels = [
        ("success_rate", "Success rate (reached the exit)"),
        ("avg_steps", "Average steps per try (lower is better)"),
        ("avg_reward", "Average points per try"),
        ("epsilon", "Random-move rate"),
    ]
    has_loss = False
    for row in rows:
        if row.get("loss") is not None:
            has_loss = True
    if has_loss:
        panels.append(("loss", "Error (how far off the scores were)"))

    columns = 2
    grid_rows = (len(panels) + columns - 1) // columns
    figure, axes = plt.subplots(grid_rows, columns, figsize=(10, 3 * grid_rows), squeeze=False)

    flat_axes = []
    for axes_row in axes:
        flat_axes.extend(axes_row)

    for index, axis in enumerate(flat_axes):
        if index >= len(panels):
            axis.set_visible(False)
            continue
        name, label = panels[index]
        points_x = []
        points_y = []
        for row in rows:
            if row.get(name) is not None:
                points_x.append(row["episode"])
                points_y.append(row[name])
        axis.plot(points_x, points_y, linewidth=1.5)
        axis.set_title(label, fontsize=10)
        axis.set_xlabel("Try number")
        axis.grid(alpha=0.3)

    if title:
        figure.suptitle(f"{title}: {episodes[-1] if episodes else 0} tries")
    figure.tight_layout()
    out = Path(out_path)
    figure.savefig(out, dpi=120)
    plt.close(figure)
    return out
