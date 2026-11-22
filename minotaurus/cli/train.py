"""`minotaurus train --config <file>`: train a brain and write brain.onnx."""

import argparse
import sys


def add_parser(commands) -> None:
    parser = commands.add_parser("train", help="train a brain and write brain.onnx")
    parser.add_argument("--config", required=True, help="path to a brain config .json")
    parser.add_argument("--runs-dir", default="runs", help="where runs are written (default runs)")
    parser.add_argument("--log-every", type=int, default=10, help="episodes per metrics line")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
    from minotaurus.trainer.config import ConfigError, load_config
    from minotaurus.trainer.train import train

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"minotaurus: bad config: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    def show(line: dict) -> None:
        print(
            f"episode {line['episode']}/{config.episodes}  reward {line['avg_reward']:.3f}  "
            f"steps {line['avg_steps']:.1f}  success {line['success_rate']:.0%}  "
            f"epsilon {line['epsilon']:.3f}"
        )

    run_dir = train(config, args.runs_dir, log_every=args.log_every, progress=show)
    print(f"brain written: {run_dir / 'brain.onnx'}")
