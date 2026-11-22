import pytest

from cli import main


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
    from cli import dev_commands

    (server, _), (page, web_dir) = dev_commands(8123)
    assert "serve" in server and "8123" in server
    assert page == ["bun", "run", "dev"] and web_dir.endswith("web")


def test_check_brain_and_play_with_brain(tmp_path, capsys, monkeypatch):
    import sys

    import cli
    from minotaurus.trainer.export import export_qtable
    from minotaurus.trainer.qtable import QTableAgent

    path = tmp_path / "q.onnx"
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "tiny", ["easy-01"])
    monkeypatch.setattr(sys, "argv", ["minotaurus", "check-brain", str(path)])
    cli.main()
    assert "OK: tiny (qtable)" in capsys.readouterr().out

    bad = tmp_path / "bad.onnx"
    bad.write_bytes(b"x" * 1_000_001)
    monkeypatch.setattr(sys, "argv", ["minotaurus", "check-brain", str(bad)])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "REJECTED: file is too big" in capsys.readouterr().out


def test_dev_mock_runs_only_the_mock_page():
    from cli import dev_commands

    commands = dev_commands(8000, mock=True)
    assert [c for c, _ in commands] == [["bun", "run", "dev:mock"]]
