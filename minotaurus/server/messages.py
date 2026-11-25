"""The messages between the server and the page. The Python twin of web/src/protocol.ts.

Both sides check the same samples (data/schemas/message-samples.json), so a drift fails a test.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Point(_Strict):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class RunStarted(_Strict):
    type: Literal["run_started"]
    level_id: str
    start: Point
    step_limit: int = Field(ge=1)


class Tick(_Strict):
    type: Literal["tick"]
    n: int = Field(ge=1)
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class Result(_Strict):
    type: Literal["result"]
    status: Literal["finished", "timed_out", "stuck", "error"]
    steps: int = Field(ge=0)
    seconds: float = Field(ge=0)
    # finished runs only: steps divided by the shortest path (1.0 = the shortest way, 2.0 = twice as long)
    path_ratio: float | None = Field(default=None, ge=1)
    message: str | None = None


class ErrorMessage(_Strict):
    type: Literal["error"]
    message: str


# One message of a run; the "type" field says which one it is.
RunMessage = Annotated[RunStarted | Tick | Result | ErrorMessage, Field(discriminator="type")]


GridRow = Annotated[str, StringConstraints(pattern=r"^[#.SE]+$")]


class LevelInfo(_Strict):
    id: str
    name: str
    difficulty: Literal["easy", "medium", "hard", "impossible"]
    # Where the level comes from; the page draws one heading per group.
    group: Literal["hand-made", "test"] = "hand-made"
    grid: list[GridRow] = Field(min_length=1)
    step_limit: int = Field(ge=1)


HexId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Fingerprint = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{16}$")]


class BrainResponse(_Strict):
    """One loaded brain. `id` is the sha256 of its brain.onnx (the page shows the first 8)."""

    id: HexId
    name: str
    method: Literal["qtable", "dqn"]
    has_recipe: bool  # True when it came in a bundle (settings, scores and graph are known)
    added_at: str  # ISO date and time


class Scores(_Strict):
    train: float = Field(ge=0, le=1)
    validation: float = Field(ge=0, le=1)
    test: float = Field(ge=0, le=1)


class TestStats(_Strict):
    __test__ = False  # not a pytest class
    avg_steps: float = Field(ge=0)
    avg_path_ratio: float | None = Field(default=None, ge=1)


class BrainRecipe(_Strict):
    """What a bundle says about how its brain was made."""

    bundle_version: int = Field(ge=1)
    # The training config, already checked as a ConfigFile (data/schemas/brain-config.schema.json).
    config: dict[str, Any]
    scores: Scores | None = None
    fixed_levels: dict[str, bool] | None = None
    test_stats: TestStats | None = None
    has_graph: bool
    # The author's id (fingerprint of the signing key) when the bundle is signed and the signature
    # is good, and when this server first saw that author. Unsigned bundles have neither.
    signed_by: Fingerprint | None = None
    author_first_seen: str | None = None


class MetricPoint(_Strict):
    """One training line: how the last few tries went. A value the run did not record is left out."""

    episode: int = Field(ge=0)
    success_rate: float | None = Field(default=None, ge=0, le=1)
    avg_steps: float | None = Field(default=None, ge=0)
    avg_reward: float | None = None
    epsilon: float | None = Field(default=None, ge=0, le=1)
    loss: float | None = Field(default=None, ge=0)


class QuizPoint(_Strict):
    """One quiz (validation) check during training."""

    episode: int = Field(ge=0)
    validation_success: float = Field(ge=0, le=1)


class BrainMetrics(_Strict):
    """What the page needs to draw a brain's training curves (from metrics.jsonl in its bundle)."""

    points: list[MetricPoint]
    quiz: list[QuizPoint]
    saved_at: int | None = Field(default=None, ge=0)  # the try the saved brain came from


class VerifyCheck(_Strict):
    """One claim of a bundle, checked again by the server."""

    name: str
    claimed: float | None = None
    actual: float | None = None
    match: bool


class Verification(_Strict):
    """Did the scores a bundle claims come out the same when the server plays the brain itself?"""

    status: Literal["verified", "mismatch", "unavailable"]
    message: str
    checks: list[VerifyCheck]
    not_checked: list[str]  # claims the server did not repeat (the training pile: too slow)


class LevelResult(_Strict):
    """How a brain did on one portal level in a "run all levels" batch."""

    level_id: str
    name: str
    group: Literal["hand-made", "test"]
    status: Literal["finished", "timed_out", "stuck", "error"]
    steps: int = Field(ge=0)
    seconds: float = Field(ge=0)
    path_ratio: float | None = Field(default=None, ge=1)


class BatchResult(_Strict):
    """One "run all levels" of one brain: every portal level, played at full speed."""

    id: str = Field(min_length=1, max_length=64)
    brain_id: HexId
    date: str  # ISO date and time
    total: int = Field(ge=0)
    finished: int = Field(ge=0)
    results: list[LevelResult]
