from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from dg_kit.commands import (
    sync,
    test,
    pull
)

DEFAULT_CONFIG_FILE = "dg_kit.yml"
SUPPORTED_COMMANDS = ("test", "sync", "pull")


def _load_config(config_path: str | None = None) -> dict[str, Any]:
    print(f"loading config from {config_path}")
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        raise ValueError("Config file must define a YAML object at the top level")

    return config


def build_parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(prog="dg_kit")
    
    command_parser.add_argument("command", choices=SUPPORTED_COMMANDS)

    command_parser.add_argument(
        "--config",
        help=("Path to YAML config. If omitted, ./dg_kit.yml is used when present"),
        default=str(Path.cwd() / DEFAULT_CONFIG_FILE)
    )

    command_parser.add_argument(
        "--release",
        help=(
            "Path to YAML config. If omitted, ./dg_kit.release.yml is used when present"
        ),
    )

    return command_parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = _load_config(args.config)

    if args.command == 'sync':
        release_config = _load_config(args.release)
        sync.run(config, release_config)
    
    elif args.command == 'test':
        test.run(config)
    
    elif args.command == 'pull':
        pull.run(config)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
