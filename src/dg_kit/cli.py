from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import yaml

from dg_kit.commands import sync, test, pull

DEFAULT_CONFIG_FILE = "dg_kit.yml"
SUPPORTED_COMMANDS = ("test", "sync", "pull")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

logger = logging.getLogger(__name__)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )


def _load_config(config_path: str | None = None) -> dict[str, Any]:
    logger.info("Loading config from %s", config_path)
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
        default=str(Path.cwd() / DEFAULT_CONFIG_FILE),
    )

    command_parser.add_argument(
        "--convention",
        help=(
            "Path to YAML config. If omitted, ./dg_kit.convention.yml is used when present"
        ),
    )

    command_parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="INFO",
        help="Logging level for CLI output.",
    )

    return command_parser


def main(argv: list[str] | None = None) -> int:
    sys_exit_status = 0

    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.log_level)

    config = _load_config(args.config)

    if args.command == "sync":
        sys_exit_status = sync.run(config)

    elif args.command == "test":
        convention_config = _load_config(args.convention)
        sys_exit_status = test.run(config, convention_config)

    elif args.command == "pull":
        sys_exit_status = pull.run(config)

    return sys_exit_status


if __name__ == "__main__":
    raise SystemExit(main())
