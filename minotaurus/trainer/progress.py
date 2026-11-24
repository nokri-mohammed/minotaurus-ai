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


def _fit(columns: int | None, rest: str, done: int, total: int) -> str:
    """The bar and `rest` on one line that is never wider than the terminal.

    A line wider than the terminal wraps, and then redrawing in place leaves leftovers. So the
    bar gets shorter on a narrow terminal (down to 5 cells), and the text is cut as a last resort.
    """
    width = 20
    if columns is not None:
        room = columns - 1 - len(rest) - 3  # 3 = the two brackets and the space after the bar
        width = max(5, min(20, room))
    line = f"{bar(done, total, width)} {rest}"
    if columns is not None and len(line) > columns - 1:
        return line[: columns - 1]
    return line


def single_line(
    episode: int, total: int, elapsed: float, success_rate: float, columns: int | None = None
) -> str:
    """One run. Example: "[████░░░░░░░░░░░░░░░░] 25%  try 250/1000  success 40%  left 30.0 s"."""
    rest = (
        f"{percent(episode, total)}%  try {episode}/{total}  "
        f"success {success_rate:.0%}{_left_text(elapsed, episode, total)}"
    )
    return _fit(columns, rest, episode, total)


def multi_line(
    episodes: dict[int, int],
    per_seed: int,
    finished: int,
    elapsed: float,
    columns: int | None = None,
) -> str:
    """Several seeds: one bar for all of them.

    `episodes` is seed -> tries done so far. Example with 3 seeds of 100 tries, one done and one
    half way: 150 of 300 tries, 50%.
    """
    total = per_seed * len(episodes)
    done = 0
    for count in episodes.values():
        done += count
    rest = (
        f"{percent(done, total)}%  seeds done {finished}/{len(episodes)}"
        f"{_left_text(elapsed, done, total)}"
    )
    return _fit(columns, rest, done, total)
