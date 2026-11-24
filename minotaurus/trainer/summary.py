"""The short report printed when a training run ends."""

from __future__ import annotations

from pathlib import Path

from minotaurus.trainer.plot import read_metrics


def format_duration(seconds: float) -> str:
    """Example: 4.26 -> "4.3 s"; 65 -> "1 min 5 s"; 3725 -> "1 h 2 min 5 s"."""
    if seconds < 60:
        return f"{seconds:.1f} s"
    whole = round(seconds)
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    if hours > 0:
        return f"{hours} h {minutes} min {secs} s"
    return f"{minutes} min {secs} s"


def summarize_run(run_dir: str | Path, seconds: float) -> list[str]:
    """Lines to print after training: the time taken and the last numbers.

    (The exported try and the maze scores are printed by the train command just before.)

    "Last numbers" are from the final logging window, so they show how the brain ended, not an
    average over the whole run.
    """
    run_dir = Path(run_dir)
    last = None
    for row in read_metrics(run_dir / "metrics.jsonl"):
        if "avg_steps" in row:
            last = row
    lines = ["", "Training summary", f"  time taken     {format_duration(seconds)}"]
    if last is not None:
        lines.append(f"  tries          {last['episode']} tries")
        lines.append(f"  finished       {last['success_rate']:.0%} of the last tries")
        lines.append(f"  steps          {last['avg_steps']:.1f} on average")
        ratio = last.get("avg_path_ratio")
        if ratio is None:
            lines.append("  path length    none finished, so no path length")
        else:
            lines.append(f"  path length    {ratio:.2f} x the shortest way (1.00 is the shortest)")
        if "parameters" in last:
            lines.append(f"  brain size     {last['parameters']} numbers")
    return lines
