from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_FILE = "dg_kit.release.yml"
SUPPORTED_COMMANDS = ("test", "sync")


def _load_config(config_path: str | None) -> dict[str, Any]:
    print(f"loading config from {config_path}")
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        raise ValueError("Config file must define a YAML object at the top level")

    return config


def _run_command(
    command_name: str, config: dict[str, Any], release: dict[str, Any]
) -> None:
    module = importlib.import_module(f"dg_kit.commands.{command_name}")
    flow_run = getattr(module, "run", None)
    if flow_run is None:
        raise AttributeError(f"No such command: 'dg_kit.commands.{command_name}'")

    flow_run(config, release)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dg_kit")
    command_parser = parser.add_subparsers(dest="command", required=True)

    run_parser = command_parser.add_parser("run", help="Run a command")
    run_parser.add_argument("command", choices=SUPPORTED_COMMANDS)
    run_parser.add_argument(
        "--config",
        help=("Path to YAML config. If omitted, ./dg_kit.yml is used when present"),
    )
    run_parser.add_argument(
        "--release",
        help=(
            "Path to YAML config. If omitted, ./dg_kit.release.yml is used when present"
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = _load_config(args.config)
    release_config = _load_config(args.release)
    _run_command(args.command, config, release_config)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
