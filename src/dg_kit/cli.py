"""Command-line entry points for ``dg_kit`` workflows.

This module builds the argument parser, loads YAML configuration, and
dispatches supported commands.
"""

from __future__ import annotations

import argparse
import logging
from importlib.metadata import version
from pathlib import Path
from typing import Any

import yaml

from dg_kit.commands import test
from dg_kit.commands.data_catalog import pull, sync

DEFAULT_CONFIG_FILE = "dg_kit.yml"
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

logger = logging.getLogger(__name__)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )


def _load_config(config_path: str | None = None) -> dict[str, Any]:
    if config_path is None:
        raise ValueError(
            "No config path provided. Use --config or --convention to specify one."
        )

    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        raise ValueError("Config file must define a YAML object at the top level")

    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dg_kit", description="Data Governance Toolkit CLI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('dg_kit')}",
    )
    parser.add_argument(
        "--config",
        help=("Path to YAML config. If omitted, ./dg_kit.yml is used when present"),
        default=str(Path.cwd() / DEFAULT_CONFIG_FILE),
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="INFO",
        help="Logging level for CLI output.",
    )
    command_parser = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )

    # dg_kit test --convention ./my_convention.yml
    test = command_parser.add_parser("test", help="Test commands")
    test.add_argument(
        "--convention",
        default=str(Path.cwd() / "dg_kit.convention.yml"),
        help="Path to convention YAML config. Defaults to ./dg_kit.convention.yml.",
    )

    # dg_kit data-catalog pull/sync
    data_catalog = command_parser.add_parser(
        "data-catalog", help="Data catalog commands"
    )
    data_catalog_subparsers = data_catalog.add_subparsers(
        dest="data_catalog_command",
        required=True,
    )
    data_catalog_subparsers.add_parser("pull", help="Pull data catalog to local.")
    data_catalog_subparsers.add_parser(
        "sync",
        help="Sync Logical Model, Business Information and Physical model with Data Catalog.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    sys_exit_status = 0

    parser = build_parser()
    args = parser.parse_args(argv)

    config = _load_config(args.config)

    _configure_logging(args.log_level)

    if args.command == "test":
        convention_config = _load_config(args.convention)
        sys_exit_status = test.run(config, convention_config)

    elif args.command == "data-catalog":
        if args.data_catalog_command == "pull":
            sys_exit_status = pull.run(config)
        elif args.data_catalog_command == "sync":
            sys_exit_status = sync.run(config)

    return sys_exit_status


if __name__ == "__main__":
    raise SystemExit(main())
