"""The local arena server: levels, one uploaded brain, and a streamed run. Binds 127.0.0.1 only."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from minotaurus import __version__, brain, engine, trainer
from minotaurus.brain import BrainError, load_brain, player
from minotaurus.brain.onnx_brain import MAX_BYTES
from minotaurus.engine.levels import LevelError, load_portal_levels, select_by_ids
from minotaurus.engine.race import TICK_SECONDS
from minotaurus.server.arena import run_arena
from minotaurus.server.messages import BrainResponse, ErrorMessage, LevelInfo


def _refused(message: str) -> JSONResponse:
    """A refused request: HTTP 400 with {"message": ...}, which the page shows to the player."""
    return JSONResponse(status_code=400, content={"message": message})


def create_app(tick_seconds: float = TICK_SECONDS) -> FastAPI:
    """Build the server. `tick_seconds` is the real pause between ticks; tests pass 0."""
    app = FastAPI(title="minotaurus-ai", version=__version__)
    app.state.brain = None  # the one uploaded brain: a callable obs -> move
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
        infos = []
        for level in load_portal_levels():
            infos.append(
                LevelInfo(
                    id=level.id,
                    name=level.name,
                    difficulty=level.difficulty,
                    grid=list(level.grid),
                    step_limit=level.step_limit,
                )
            )
        return infos

    @app.post("/api/brain")
    async def upload_brain(file: UploadFile):
        # Read one byte more than the limit, so a huge upload is never read in full.
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return _refused(f"file is too big: more than {MAX_BYTES} bytes")

        # The loader works on a file path, so the upload goes to a temporary file first.
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "brain.onnx"
            path.write_bytes(data)
            try:
                loaded = load_brain(path)
            except BrainError as exc:
                return _refused(str(exc))

        name = loaded.name or Path(file.filename or "brain").stem
        try:
            info = BrainResponse(name=name, method=loaded.method)
        except ValidationError:
            return _refused(f"unknown training method {loaded.method!r}")

        # Only a good brain replaces the loaded one; a refused upload keeps the old brain.
        app.state.brain = loaded
        return info

    @app.websocket("/ws/run")
    async def ws_run(websocket: WebSocket, level_id: str = ""):
        await websocket.accept()
        try:
            await _stream_run(websocket, level_id)
        except WebSocketDisconnect:
            pass  # the page closed the socket mid-run: stop quietly

    async def _stream_run(websocket: WebSocket, level_id: str) -> None:
        async def send_error(text: str) -> None:
            message = ErrorMessage(type="error", message=text)
            await websocket.send_text(message.model_dump_json())
            await websocket.close()

        if app.state.running:
            await send_error("A run is already in progress.")
            return
        if app.state.brain is None:
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
            loaded = app.state.brain
            mover = player(loaded, seed=f"{getattr(loaded, 'digest', '')}|{level.id}")
            async for message in run_arena(level, mover, tick_seconds):
                await websocket.send_text(message.model_dump_json(exclude_none=True))
            await websocket.close()
        finally:
            app.state.running = False  # also when the page disconnects mid-run

    return app


app = create_app()
