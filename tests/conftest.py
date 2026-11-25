import pytest

from minotaurus.engine.levels import Level, parse_level


def make_level(rows: list[str], **extra) -> Level:
    data = {"id": "t-01", "name": "Test", "difficulty": "easy", "grid": rows}
    data.update(extra)
    return parse_level(data)


@pytest.fixture
def corridor() -> Level:
    # S . . E in a straight line, one row, walls around
    return make_level(["#####", "#S.E#", "#####"])


@pytest.fixture
def open_room() -> Level:
    return make_level(
        [
            "#######",
            "#S....#",
            "#.....#",
            "#....E#",
            "#######",
        ]
    )


@pytest.fixture(autouse=True)
def no_real_signing_key(monkeypatch, tmp_path_factory):
    """Tests never sign with the developer's own key: point the default at a file that is not there."""
    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(tmp_path_factory.getbasetemp() / "no-key.key"))
