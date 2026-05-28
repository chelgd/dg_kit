"""Implementation of the ``dg_kit pull`` command.

This module downloads the current data catalog state from the configured
remote backend and persists the local checkpoint.
"""

from __future__ import annotations

from typing import Any

from os import environ

from dg_kit.base.data_catalog import DataCatalog
from dg_kit.integrations.notion.api import NotionDataCatalog


def run(
    config: dict[str, Any],
) -> None:
    config["data_catalog"]["notion_token"] = environ["NOTION_TOKEN"]
    config["data_catalog"]["dc_table_id"] = environ["DATA_CATALOG_ID"]

    ndc_engine = NotionDataCatalog(
        notion_config=config["data_catalog"],
    )

    DC = DataCatalog(
        engine=ndc_engine,
        config=config,
    )

    DC.pull_data_catalog()
