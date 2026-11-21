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


def test_dev_starts_server_and_page_on_localhost():
    from minotaurus.cli import dev_commands

    (server, _), (page, web_dir) = dev_commands(8123)
    assert "serve" in server and "8123" in server
    assert page == ["bun", "run", "dev"] and web_dir.endswith("web")
