"""The progress line shown while training: a bar, the percent and the time left."""

from __future__ import annotations

from minotaurus.trainer.summary import format_duration

FULL = "█"
EMPTY = "░"


def percent(done: int, total: int) -> int:
    """Whole percent, never above 100. Example: percent(252, 600) -> 42."""
    if total <= 0:
        return 100
    value = done * 100 // total
    if value > 100:
        return 100
    return value


def bar(done: int, total: int, width: int = 20) -> str:
    """Example: bar(5, 10, 10) -> "[█████░░░░░]"."""
    filled = percent(done, total) * width // 100
    return "[" + FULL * filled + EMPTY * (width - filled) + "]"


def time_left(elapsed: float, done: int, total: int) -> str | None:
    """Time left from the speed so far; None before any progress or when finished.

    Example: 25 of 100 done in 10 s -> the other 75 take "30.0 s".
    """
    if done <= 0 or done >= total:
        return None
    seconds = elapsed / done * (total - done)
    return format_duration(seconds)


def _left_text(elapsed: float, done: int, total: int) -> str:
    left = time_left(elapsed, done, total)
    if left is None:
        return ""
    return f"  left {left}"


def single_line(episode: int, total: int, elapsed: float, success_rate: float) -> str:
    """One run. Example: "[████░░░░░░░░░░░░░░░░] 25%  try 250/1000  success 40%  left 30.0 s"."""
    return (
        f"{bar(episode, total)} {percent(episode, total)}%  try {episode}/{total}  "
        f"success {success_rate:.0%}{_left_text(elapsed, episode, total)}"
    )


def multi_line(episodes: dict[int, int], per_seed: int, finished: int, elapsed: float) -> str:
    """Several seeds: one bar for all of them.

    `episodes` is seed -> tries done so far. Example with 3 seeds of 100 tries, one done and one
    half way: 150 of 300 tries, 50%.
    """
    total = per_seed * len(episodes)
    done = 0
    for count in episodes.values():
        done += count
    return (
        f"{bar(done, total)} {percent(done, total)}%  seeds done {finished}/{len(episodes)}"
        f"{_left_text(elapsed, done, total)}"
    )
