from minotaurus.cli import main


def test_play_random_moves_a_dot(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "minotaurus",
            "play",
            "--level",
            "easy-01",
            "--seed",
            "1",
            "--delay",
            "0",
            "--max-steps",
            "5",
        ],
    )
    main()
    out = capsys.readouterr().out
    assert "@" in out and "step 5" in out


def test_play_unknown_level_exits(monkeypatch, capsys):
    import pytest

    monkeypatch.setattr("sys.argv", ["minotaurus", "play", "--level", "nope"])
    with pytest.raises(SystemExit):
        main()
    assert "nope" in capsys.readouterr().err
