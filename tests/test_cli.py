from typer.testing import CliRunner

from minotaurus.cli import app, dev_commands

runner = CliRunner()


def test_help_lists_every_command():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ["hello", "train", "check-brain", "play", "serve", "dev"]:
        assert name in result.output


def test_hello():
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "engine ready" in result.output


def test_play_random_moves_a_dot():
    result = runner.invoke(
        app, ["play", "--level", "easy-01", "--seed", "1", "--delay", "0", "--max-steps", "5"]
    )
    assert result.exit_code == 0
    assert "@" in result.output and "step 5" in result.output


def test_play_unknown_level_exits():
    result = runner.invoke(app, ["play", "--level", "nope"])
    assert result.exit_code == 2
    assert "nope" in result.output


def test_train_needs_a_config():
    result = runner.invoke(app, ["train"])
    assert result.exit_code != 0


def test_train_missing_config_file(tmp_path):
    result = runner.invoke(app, ["train", "--config", str(tmp_path / "missing.json")])
    assert result.exit_code == 2


def test_train_bad_config_names_the_problem(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"name": "x", "method": "ppo"}')
    result = runner.invoke(app, ["train", "--config", str(bad)])
    assert result.exit_code == 2
    assert "method" in result.output


def test_dev_starts_server_and_page_on_localhost():
    (server, _), (page, web_dir) = dev_commands(8123)
    assert "serve" in server and "8123" in server
    assert page == ["bun", "run", "dev"] and web_dir.endswith("web")


def test_check_brain_and_play_with_brain(tmp_path):
    from minotaurus.trainer.export import export_qtable
    from minotaurus.trainer.qtable import QTableAgent

    path = tmp_path / "q.onnx"
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "tiny", ["easy-01"])
    ok = runner.invoke(app, ["check-brain", str(path)])
    assert ok.exit_code == 0
    assert "OK: tiny (qtable)" in ok.output

    bad = tmp_path / "bad.onnx"
    bad.write_bytes(b"x" * 1_000_001)
    rejected = runner.invoke(app, ["check-brain", str(bad)])
    assert rejected.exit_code == 1
    assert "REJECTED: file is too big" in rejected.output
