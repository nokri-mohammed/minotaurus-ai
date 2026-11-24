"""`minotaurus serve`."""

from typing import Annotated

import typer


def run(port: Annotated[int, typer.Option(help="Port on 127.0.0.1.")] = 8000) -> None:
    import uvicorn

    uvicorn.run("minotaurus.server.app:make_app", factory=True, host="127.0.0.1", port=port)
