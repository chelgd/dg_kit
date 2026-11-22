"""Helpers shared by ``dg_kit`` commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dg_kit.base.physical_model import PhysicalModel
from dg_kit.integrations.dbt.parser import DBTParser


def parse_physical_model(config: dict[str, Any]) -> PhysicalModel:
    """Build the physical model described by the ``physical_model`` config section.

    Reads ``path`` and the optional ``source_paths`` and ``ignore`` keys. Relative
    paths are resolved from the current working directory.

    :param config: Project configuration with model locations and version info.
    :type config: dict[str, Any]
    :returns: Parsed physical model.
    :rtype: PhysicalModel
    """
    pm_config = config.get("physical_model", {})

    dbt_parser = DBTParser(
        Path(pm_config.get("path")),
        config["version"],
        source_paths=pm_config.get("source_paths"),
        ignore=pm_config.get("ignore"),
    )
    return dbt_parser.parse_pm()
