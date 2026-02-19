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

    DataCatalog(
        engine=ndc_engine,
        config=config,
        pull=True
    )
