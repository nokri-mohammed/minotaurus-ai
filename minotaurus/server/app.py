"""The local arena server: levels, one uploaded brain, and a streamed run. Binds 127.0.0.1 only."""

from __future__ import annotations

import hashlib
import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from minotaurus import __version__, brain, engine, trainer
from minotaurus.brain import BrainError, load_brain, player
from minotaurus.brain.onnx_brain import MAX_BYTES
from minotaurus.bundle import MAX_BUNDLE_BYTES, BundleError, read_bundle
from minotaurus.engine.levels import (
    LevelError,
    load_portal_levels,
    load_test_mazes,
    select_by_ids,
)
from minotaurus.engine.race import TICK_SECONDS
from minotaurus.server.arena import run_arena
from minotaurus.server.messages import (
    BatchResult,
    BrainRecipe,
    BrainResponse,
    ErrorMessage,
    LevelInfo,
    LevelResult,
    Scores,
    TestStats,
)
from minotaurus.server.store import Store

HEX_ID = re.compile(r"^[0-9a-f]{64}$")
DATA_DIR = Path("var")


def _is_tar(data: bytes) -> bool:
    """A tar file has "ustar" at byte 257; an .onnx file never does."""
    return data[257:262] == b"ustar"


def _load_onnx_bytes(data: bytes):
    """The loader works on a file path, so the bytes go to a temporary file first."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "brain.onnx"
        path.write_bytes(data)
        return load_brain(path)


def _brain_row(row: dict) -> BrainResponse:
    return BrainResponse(
        id=row["id"],
        name=row["name"],
        method=row["method"],
        has_recipe=row["kind"] == "bundle",
        added_at=row["added_at"],
    )


def _refused(message: str) -> JSONResponse:
    """A refused request: HTTP 400 with {"message": ...}, which the page shows to the player."""
    return JSONResponse(status_code=400, content={"message": message})


def create_app(tick_seconds: float = TICK_SECONDS, data_dir: Path | None = None) -> FastAPI:
    """Build the server. `tick_seconds` is the real pause between ticks; tests pass 0.

    `data_dir` holds arena.db (loaded brains and batches); None keeps them in memory only.
    """
    app = FastAPI(title="minotaurus-ai", version=__version__)
    store = Store(None if data_dir is None else Path(data_dir) / "arena.db")
    app.state.store = store
    app.state.brain = None  # the brain loaded last: used by a run that names no brain id
    app.state.loaded = {}  # brain id -> loaded brain, filled on upload and from the store

    def find_brain(brain_id: str):
        """A loaded brain by id: from memory, else rebuilt from the stored file. None if unknown."""
        if brain_id in app.state.loaded:
            return app.state.loaded[brain_id]
        found = store.get_brain_data(brain_id)
        if found is None:
            return None
        kind, data = found
        if kind == "bundle":
            data = read_bundle(data).files["brain.onnx"]
        loaded = _load_onnx_bytes(data)
        app.state.loaded[brain_id] = loaded
        return loaded

    app.state.running = False  # one run at a time

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {
            "message": "Hello from the minotaurus server",
            "engine": engine.hello(),
            "trainer": trainer.hello(),
            "brain": brain.hello(),
        }

    @app.get("/api/levels")
    def levels() -> list[LevelInfo]:
        test_ids = []
        for test_maze in load_test_mazes():
            test_ids.append(test_maze.id)
        infos = []
        for level in load_portal_levels():
            group = "hand-made"
            if level.id in test_ids:
                group = "test"
            infos.append(
                LevelInfo(
                    id=level.id,
                    name=level.name,
                    difficulty=level.difficulty,
                    group=group,
                    grid=list(level.grid),
                    step_limit=level.step_limit,
                )
            )
        return infos

    @app.post("/api/brain")
    async def upload_brain(file: UploadFile):
        # Read one byte more than the limit, so a huge upload is never read in full.
        data = await file.read(MAX_BUNDLE_BYTES + 1)
        kind = "onnx"
        onnx_bytes = data
        if _is_tar(data):
            kind = "bundle"
            try:
                bundle = read_bundle(data)
            except BundleError as exc:
                return _refused(str(exc))
            onnx_bytes = bundle.files["brain.onnx"]
        elif len(data) > MAX_BYTES:
            return _refused(f"file is too big: more than {MAX_BYTES} bytes")

        try:
            loaded = _load_onnx_bytes(onnx_bytes)
        except BrainError as exc:
            return _refused(str(exc))

        name = loaded.name or Path(file.filename or "brain").stem
        brain_id = hashlib.sha256(onnx_bytes).hexdigest()
        if loaded.method not in ("qtable", "dqn"):
            return _refused(f"unknown training method {loaded.method!r}")
        store.add_brain(brain_id, name, loaded.method, kind, data)
        # Only a good brain is kept; a refused upload changes nothing.
        app.state.loaded[brain_id] = loaded
        app.state.brain = loaded
        for row in store.list_brains():
            if row["id"] == brain_id:
                return _brain_row(row)
        return _refused("the brain could not be saved")

    @app.get("/api/brains")
    def list_brains() -> list[BrainResponse]:
        brains = []
        for row in store.list_brains():
            brains.append(_brain_row(row))
        return brains

    def read_recipe_bundle(brain_id: str):
        """The bundle of a brain, or None when the id is unknown or the brain came as plain .onnx."""
        if not HEX_ID.match(brain_id):
            return None
        found = store.get_brain_data(brain_id)
        if found is None or found[0] != "bundle":
            return None
        return read_bundle(found[1])

    @app.get("/api/brains/{brain_id}/recipe")
    def brain_recipe(brain_id: str):
        bundle = read_recipe_bundle(brain_id)
        if bundle is None:
            return JSONResponse(status_code=404, content={"message": "no recipe for this brain"})
        scores = None
        raw_scores = bundle.json_file("scores.json")
        if raw_scores is not None:
            try:
                scores = Scores.model_validate(raw_scores)
            except ValidationError:
                scores = None
        stats = None
        raw_stats = bundle.json_file("test_stats.json")
        if raw_stats is not None:
            try:
                stats = TestStats.model_validate(raw_stats)
            except ValidationError:
                stats = None
        return BrainRecipe(
            bundle_version=bundle.manifest.version,
            config=bundle.config.model_dump(mode="json", exclude_unset=True),
            scores=scores,
            fixed_levels=bundle.json_file("fixed_levels.json"),
            test_stats=stats,
            has_graph="training.png" in bundle.files,
        )

    @app.get("/api/brains/{brain_id}/graph.png")
    def brain_graph(brain_id: str):
        bundle = read_recipe_bundle(brain_id)
        if bundle is None or "training.png" not in bundle.files:
            return JSONResponse(status_code=404, content={"message": "no graph for this brain"})
        return Response(content=bundle.files["training.png"], media_type="image/png")

    @app.post("/api/brains/{brain_id}/run-all", response_model_exclude_none=True)
    async def run_all_levels(brain_id: str):
        """Play every portal level with this brain at full speed (no pauses) and keep the result."""
        if app.state.running:
            return _refused("A run is already in progress.")
        chosen = None
        if HEX_ID.match(brain_id):
            chosen = find_brain(brain_id)
        if chosen is None:
            return JSONResponse(status_code=404, content={"message": "That brain is not loaded."})

        test_ids = []
        for test_maze in load_test_mazes():
            test_ids.append(test_maze.id)
        results = []
        finished = 0
        app.state.running = True
        try:
            for level in load_portal_levels():
                # The same seed as a run by hand, so a level gives the same result both ways.
                mover = player(chosen, seed=f"{chosen.digest}|{level.id}")
                last = None
                async for message in run_arena(level, mover, 0.0):
                    last = message
                group = "hand-made"
                if level.id in test_ids:
                    group = "test"
                if last is None or last.type != "result":
                    continue
                if last.status == "finished":
                    finished += 1
                results.append(
                    LevelResult(
                        level_id=level.id,
                        name=level.name,
                        group=group,
                        status=last.status,
                        steps=last.steps,
                        seconds=last.seconds,
                        path_ratio=last.path_ratio,
                    )
                )
        finally:
            app.state.running = False
        batch = BatchResult(
            id=uuid.uuid4().hex,
            brain_id=brain_id,
            date=datetime.now(UTC).isoformat(timespec="seconds"),
            total=len(results),
            finished=finished,
            results=results,
        )
        # Empty fields are left out (a level that did not finish has no path_ratio), as the page expects.
        body = batch.model_dump(mode="json", exclude_none=True)
        store.add_batch(body)
        return JSONResponse(content=body)

    @app.get("/api/brains/{brain_id}/batches", response_model_exclude_none=True)
    def list_batches(brain_id: str) -> list[BatchResult]:
        batches = []
        if not HEX_ID.match(brain_id):
            return batches
        for row in store.list_batches(brain_id):
            batches.append(BatchResult(**row))
        return batches

    @app.websocket("/ws/run")
    async def ws_run(websocket: WebSocket, level_id: str = "", brain_id: str = ""):
        await websocket.accept()
        try:
            await _stream_run(websocket, level_id, brain_id)
        except WebSocketDisconnect:
            pass  # the page closed the socket mid-run: stop quietly

    async def _stream_run(websocket: WebSocket, level_id: str, brain_id: str) -> None:
        async def send_error(text: str) -> None:
            message = ErrorMessage(type="error", message=text)
            await websocket.send_text(message.model_dump_json())
            await websocket.close()

        if app.state.running:
            await send_error("A run is already in progress.")
            return
        chosen = app.state.brain
        if brain_id:
            chosen = find_brain(brain_id)
            if chosen is None:
                await send_error("That brain is not loaded. Load it again.")
                return
        if chosen is None:
            await send_error("Load a brain (.onnx) first.")
            return
        try:
            level = select_by_ids(load_portal_levels(), [level_id])[0]
        except LevelError as exc:
            await send_error(str(exc))
            return

        app.state.running = True
        try:
            # A brain with policy_epsilon makes some random moves; the seed (brain file and level)
            # makes every run of the same brain on the same level the same, so it can be replayed.
            loaded = chosen
            mover = player(loaded, seed=f"{getattr(loaded, 'digest', '')}|{level.id}")
            async for message in run_arena(level, mover, tick_seconds):
                await websocket.send_text(message.model_dump_json(exclude_none=True))
            await websocket.close()
        finally:
            app.state.running = False  # also when the page disconnects mid-run

    return app


app = create_app()  # in memory: tests and imports


def make_app() -> FastAPI:
    """The app `minotaurus serve` runs: brains and "run all levels" batches are kept in var/arena.db."""
    return create_app(data_dir=DATA_DIR)
