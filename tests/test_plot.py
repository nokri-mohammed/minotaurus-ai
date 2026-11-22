import json
from pathlib import Path

from typer.testing import CliRunner

from minotaurus.cli import app
from minotaurus.trainer.plot import plot_metrics, read_metrics

runner = CliRunner()
EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


def write_metrics(path, with_loss):
    lines = []
    for episode in (10, 20, 30):
        line = {
            "episode": episode,
            "avg_reward": 0.1 * episode / 10,
            "avg_steps": 50.0 - episode,
            "success_rate": episode / 30,
            "epsilon": 1.0 - episode / 40,
            "loss": 0.5 if with_loss else None,
        }
        lines.append(json.dumps(line))
    path.write_text("\n".join(lines) + "\n")


def test_read_metrics_gives_one_dict_per_line(tmp_path):
    path = tmp_path / "metrics.jsonl"
    write_metrics(path, with_loss=False)
    rows = read_metrics(path)
    assert len(rows) == 3
    assert rows[0]["episode"] == 10


def test_plot_writes_a_png_for_a_qtable_run(tmp_path):
    path = tmp_path / "metrics.jsonl"
    write_metrics(path, with_loss=False)
    out = tmp_path / "training.png"
    plot_metrics(path, out, title="qtable-easy")
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_plot_writes_a_png_for_a_dqn_run_with_loss(tmp_path):
    path = tmp_path / "metrics.jsonl"
    write_metrics(path, with_loss=True)
    out = tmp_path / "training.png"
    plot_metrics(path, out, title="dqn-easy")
    assert out.exists()


def small_config(tmp_path):
    cfg = json.loads((EXAMPLES / "qtable-brain.json").read_text())
    cfg["episodes"] = 20
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    return path


def test_train_draws_the_graph_by_default(tmp_path):
    cfg = small_config(tmp_path)
    result = runner.invoke(
        app, ["train", "--config", str(cfg), "--runs-dir", str(tmp_path / "runs")]
    )
    assert result.exit_code == 0
    assert len(list((tmp_path / "runs").glob("*/*/training.png"))) == 1


def test_train_no_plot_skips_the_graph(tmp_path):
    cfg = small_config(tmp_path)
    result = runner.invoke(
        app, ["train", "--config", str(cfg), "--runs-dir", str(tmp_path / "runs"), "--no-plot"]
    )
    assert result.exit_code == 0
    assert list((tmp_path / "runs").glob("*/*/training.png")) == []
