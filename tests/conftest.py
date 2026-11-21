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
