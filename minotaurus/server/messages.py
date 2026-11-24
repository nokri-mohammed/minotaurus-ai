"""The messages between the server and the page. The Python twin of web/src/protocol.ts.

Both sides check the same samples (data/schemas/message-samples.json), so a drift fails a test.
"""

from __future__ import annotations

from typing import Annotated, Literal

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
    status: Literal["finished", "timed_out", "error"]
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
    grid: list[GridRow] = Field(min_length=1)
    step_limit: int = Field(ge=1)


class BrainResponse(_Strict):
    name: str
    method: Literal["qtable", "dqn"]
