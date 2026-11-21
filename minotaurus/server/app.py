"""FastAPI app. Skeleton: one hello endpoint the web page calls."""

from fastapi import FastAPI

from minotaurus import __version__, brain, engine, trainer

app = FastAPI(title="minotaurus-ai", version=__version__)


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {
        "message": "Hello from the minotaurus server",
        "engine": engine.hello(),
        "trainer": trainer.hello(),
        "brain": brain.hello(),
    }
