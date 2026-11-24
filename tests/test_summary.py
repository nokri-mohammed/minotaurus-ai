import json

from minotaurus.trainer.summary import format_duration, summarize_run


def test_format_duration():
    assert format_duration(4.26) == "4.3 s"
    assert format_duration(65) == "1 min 5 s"
    assert format_duration(3725) == "1 h 2 min 5 s"


def write_run(tmp_path):
    lines = [
        {
            "episode": 10,
            "avg_reward": -1.0,
            "avg_steps": 40.0,
            "success_rate": 0.1,
            "avg_path_ratio": 3.0,
            "epsilon": 0.5,
            "loss": None,
            "parameters": 40,
        },
        {
            "episode": 20,
            "avg_reward": 0.5,
            "avg_steps": 15.5,
            "success_rate": 0.9,
            "avg_path_ratio": 1.2,
            "epsilon": 0.1,
            "loss": None,
            "parameters": 80,
        },
    ]
    text = ""
    for line in lines:
        text += json.dumps(line) + "\n"
    (tmp_path / "metrics.jsonl").write_text(text)
    return tmp_path


def test_summary_shows_time_and_the_last_numbers(tmp_path):
    run = write_run(tmp_path)
    text = "\n".join(summarize_run(run, 125.0))
    assert "2 min 5 s" in text
    assert "20 tries" in text
    assert "90%" in text  # last success rate
    assert "1.2" in text  # path ratio: 1.2 x the shortest way
    assert "80" in text  # parameters
    assert "🧠" in text


def test_summary_when_nothing_finished(tmp_path):
    run = write_run(tmp_path)
    lines = (run / "metrics.jsonl").read_text().splitlines()
    last = json.loads(lines[-1])
    last["success_rate"] = 0.0
    last["avg_path_ratio"] = None
    lines[-1] = json.dumps(last)
    (run / "metrics.jsonl").write_text("\n".join(lines) + "\n")
    text = "\n".join(summarize_run(run, 3.0))
    assert "0%" in text and "none finished" in text
