from minotaurus.server.store import MAX_BRAINS, Store

ID_A = "a" * 64
ID_B = "b" * 64


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


def test_data_survives_a_new_store_on_the_same_file(tmp_path):
    first = Store(tmp_path / "arena.db")
    first.add_brain(ID_A, "one", "dqn", "onnx", b"1")
    second = Store(tmp_path / "arena.db")
    assert len(second.list_brains()) == 1
