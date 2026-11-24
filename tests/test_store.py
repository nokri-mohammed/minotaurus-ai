from minotaurus.server.store import MAX_BRAINS, Store

ID_A = "a" * 64
ID_B = "b" * 64


def attempt(attempt_id: str, brain_id: str = ID_A, date: str = "2026-11-24T10:00:00Z") -> dict:
    return {
        "id": attempt_id,
        "date": date,
        "brain_id": brain_id,
        "brain": "name",
        "method": "dqn",
        "level": "easy-01",
        "result": "finished",
        "steps": 12,
        "seconds": 1.2,
        "path": [[1, 1], [1, 2]],
    }


def test_a_brain_is_saved_and_listed_newest_first():
    store = Store()
    store.add_brain(ID_A, "one", "dqn", "onnx", b"1")
    store.add_brain(ID_B, "two", "qtable", "bundle", b"2")
    listed = store.list_brains()
    assert [row["id"] for row in listed] == [ID_B, ID_A]
    assert listed[0]["kind"] == "bundle"
    assert store.get_brain_data(ID_A) == ("onnx", b"1")


def test_the_same_brain_added_twice_is_one_row_and_a_bundle_replaces_a_plain_file():
    store = Store()
    store.add_brain(ID_A, "one", "dqn", "onnx", b"1")
    store.add_brain(ID_A, "one", "dqn", "bundle", b"tar")
    assert len(store.list_brains()) == 1
    assert store.get_brain_data(ID_A) == ("bundle", b"tar")
    store.add_brain(ID_A, "one", "dqn", "onnx", b"1")  # a plain file never hides the recipe
    assert store.get_brain_data(ID_A) == ("bundle", b"tar")


def test_an_unknown_brain_gives_none():
    assert Store().get_brain_data(ID_A) is None


def test_the_oldest_brains_are_dropped_over_the_cap():
    store = Store()
    for number in range(MAX_BRAINS + 3):
        store.add_brain(f"{number:064x}", f"b{number}", "dqn", "onnx", b"x")
    listed = store.list_brains()
    assert len(listed) == MAX_BRAINS
    assert store.get_brain_data(f"{0:064x}") is None


def test_attempts_are_saved_per_brain_newest_first():
    store = Store()
    store.add_attempt(attempt("1", ID_A, "2026-11-24T10:00:00Z"))
    store.add_attempt(attempt("2", ID_B, "2026-11-24T11:00:00Z"))
    store.add_attempt(attempt("3", ID_A, "2026-11-24T12:00:00Z"))
    mine = store.list_attempts(ID_A)
    assert [row["id"] for row in mine] == ["3", "1"]
    assert mine[0]["path"] == [[1, 1], [1, 2]]
    assert len(store.list_attempts(None)) == 3


def test_an_attempt_with_the_same_id_is_saved_once():
    store = Store()
    store.add_attempt(attempt("1"))
    store.add_attempt(attempt("1"))
    assert len(store.list_attempts(None)) == 1


def test_an_attempt_without_a_path_comes_back_without_one():
    store = Store()
    row = attempt("1")
    del row["path"]
    store.add_attempt(row)
    assert "path" not in store.list_attempts(None)[0]


def test_data_survives_a_new_store_on_the_same_file(tmp_path):
    first = Store(tmp_path / "arena.db")
    first.add_brain(ID_A, "one", "dqn", "onnx", b"1")
    first.add_attempt(attempt("1"))
    second = Store(tmp_path / "arena.db")
    assert len(second.list_brains()) == 1
    assert len(second.list_attempts(None)) == 1
