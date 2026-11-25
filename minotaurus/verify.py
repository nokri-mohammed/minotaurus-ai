"""Check a bundle's claimed scores by playing its brain again on the server.

A bundle's scores.json, fixed_levels.json and test_stats.json are written by the trainer, but
anyone can edit them and rebuild the bundle. Everything is seeded, so the same brain on the same
mazes gives the same numbers: the server regenerates the mazes from config.json, plays the brain,
and compares. The training pile is not repeated (it is the largest and not a claim of quality).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from minotaurus.brain import BrainError, load_brain
from minotaurus.bundle import BRAIN_NAME, Bundle
from minotaurus.engine.levels import LevelError
from minotaurus.server.messages import Verification, VerifyCheck
from minotaurus.trainer.evaluate import (
    POOLS_KEY,
    playthrough_stats,
    score_fixed_levels,
    success_rate,
)

TOLERANCE = 1e-6
NOT_CHECKED = ["train"]


def _same(claimed: float, actual: float) -> bool:
    return abs(claimed - actual) <= TOLERANCE


def _number_check(name: str, claimed, actual) -> VerifyCheck:
    """Compare two numbers; a claim of null must be null again."""
    if claimed is None or actual is None:
        return VerifyCheck(name=name, claimed=claimed, actual=actual, match=claimed == actual)
    return VerifyCheck(
        name=name, claimed=claimed, actual=actual, match=_same(float(claimed), float(actual))
    )


def verify_bundle(bundle: Bundle) -> Verification:
    """Play the bundle's brain again and compare with what the bundle claims."""
    claimed_scores = bundle.json_file("scores.json")
    claimed_fixed = bundle.json_file("fixed_levels.json")
    claimed_stats = bundle.json_file("test_stats.json")
    if claimed_scores is None and claimed_fixed is None and claimed_stats is None:
        return Verification(
            status="unavailable",
            message="This bundle claims no scores to check.",
            checks=[],
            not_checked=[],
        )
    config = bundle.config
    if config.pool_settings() is None:
        return Verification(
            status="unavailable",
            message="The settings name no generated mazes, so there is no exam to repeat.",
            checks=[],
            not_checked=[],
        )
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / BRAIN_NAME
        path.write_bytes(bundle.files[BRAIN_NAME])
        try:
            brain = load_brain(path)
            saved = json.loads(brain.meta.get(POOLS_KEY, "null"))
            if saved != config.pool_settings():
                return Verification(
                    status="mismatch",
                    message="The brain was trained on different mazes than the settings name.",
                    checks=[],
                    not_checked=NOT_CHECKED,
                )
            pools = config.resolve_pools()
            checks: list[VerifyCheck] = []
            if claimed_scores is not None:
                for pile in ("validation", "test"):
                    actual = success_rate(brain, getattr(pools, pile))
                    checks.append(_number_check(pile, claimed_scores.get(pile), actual))
            if claimed_fixed is not None:
                actual_fixed = score_fixed_levels(path)
                done_claimed = 0
                for finished in claimed_fixed.values():
                    if finished:
                        done_claimed += 1
                done_actual = 0
                for finished in actual_fixed.values():
                    if finished:
                        done_actual += 1
                checks.append(
                    VerifyCheck(
                        name="hand-made levels finished",
                        claimed=done_claimed,
                        actual=done_actual,
                        match=claimed_fixed == actual_fixed,
                    )
                )
            if claimed_stats is not None:
                actual_stats = playthrough_stats(path, pools.test)
                checks.append(
                    _number_check(
                        "test steps", claimed_stats.get("avg_steps"), actual_stats["avg_steps"]
                    )
                )
                checks.append(
                    _number_check(
                        "test route",
                        claimed_stats.get("avg_path_ratio"),
                        actual_stats["avg_path_ratio"],
                    )
                )
        except (BrainError, LevelError) as exc:
            return Verification(
                status="mismatch",
                message=f"The brain could not be played again: {exc}",
                checks=[],
                not_checked=NOT_CHECKED,
            )
    wrong = []
    for check in checks:
        if not check.match:
            wrong.append(check.name)
    if wrong:
        return Verification(
            status="mismatch",
            message="These claims did not come out the same: " + ", ".join(wrong) + ".",
            checks=checks,
            not_checked=NOT_CHECKED,
        )
    return Verification(
        status="verified",
        message="The server played the brain again and got the same scores.",
        checks=checks,
        not_checked=NOT_CHECKED,
    )
