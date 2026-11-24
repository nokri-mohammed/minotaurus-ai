from minotaurus.trainer.progress import bar, multi_line, percent, single_line, time_left


def test_percent_is_a_whole_number_and_never_above_100():
    assert percent(0, 600) == 0
    assert percent(252, 600) == 42
    assert percent(600, 600) == 100
    assert percent(700, 600) == 100
    assert percent(5, 0) == 100


def test_bar_fills_in_step_with_the_percent():
    assert bar(0, 10, width=10) == "[░░░░░░░░░░]"
    assert bar(5, 10, width=10) == "[█████░░░░░]"
    assert bar(10, 10, width=10) == "[██████████]"


def test_bar_is_always_the_same_width():
    for done in range(101):
        assert len(bar(done, 100, width=20)) == 22


def test_time_left_needs_some_progress_and_is_none_when_finished():
    assert time_left(10.0, 0, 100) is None
    assert time_left(10.0, 100, 100) is None


def test_time_left_follows_the_speed_so_far():
    # 25 of 100 in 10 s: 75 more take 30 s
    assert time_left(10.0, 25, 100) == "30.0 s"
    # 1 of 100 in 60 s: 99 more take 99 min
    assert time_left(60.0, 1, 100) == "1 h 39 min 0 s"


def test_single_line_shows_bar_percent_tries_success_and_time_left():
    line = single_line(episode=250, total=1000, elapsed=10.0, success_rate=0.4)
    assert "25%" in line
    assert "try 250/1000" in line
    assert "success 40%" in line
    assert "left 30.0 s" in line
    assert line.startswith("[")


def test_single_line_has_no_time_left_at_the_start():
    line = single_line(episode=0, total=1000, elapsed=0.0, success_rate=0.0)
    assert "left" not in line


def test_multi_line_adds_up_all_seeds():
    # 3 seeds of 100 tries: seed 1 done, seed 2 at 50, seed 3 at 0 -> 150 of 300 = 50%
    line = multi_line({1: 100, 2: 50, 3: 0}, per_seed=100, finished=1, elapsed=30.0)
    assert "50%" in line
    assert "seeds done 1/3" in line
    assert "left 30.0 s" in line


def test_lines_always_fit_the_terminal_width():
    for columns in (30, 40, 50, 60, 80, 120):
        single = single_line(
            episode=2500, total=5000, elapsed=1234.0, success_rate=0.5, columns=columns
        )
        assert len(single) <= columns - 1, (columns, single)
        multi = multi_line(
            {1: 2500, 2: 2500, 3: 100, 4: 0},
            per_seed=5000,
            finished=1,
            elapsed=1234.0,
            columns=columns,
        )
        assert len(multi) <= columns - 1, (columns, multi)


def test_a_wide_terminal_keeps_the_full_bar_and_a_narrow_one_a_shorter_bar():
    wide = multi_line({1: 50, 2: 0}, per_seed=100, finished=0, elapsed=5.0, columns=200)
    narrow = multi_line({1: 50, 2: 0}, per_seed=100, finished=0, elapsed=5.0, columns=50)
    assert wide.count("█") + wide.count("░") == 20
    assert narrow.count("█") + narrow.count("░") < 20
    assert "25%" in narrow
