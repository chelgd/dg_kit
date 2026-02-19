from __future__ import annotations

from typing import Any

from pathlib import Path
from os import environ

from dg_kit.base.data_catalog import DataCatalog
from dg_kit.integrations.dbt.parser import DBTParser
from dg_kit.integrations.notion.api import NotionDataCatalog
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser


def run(
    config: dict[str, Any],
    release: dict[str, Any],
) -> None:
    odm_project_path = Path(config.get("logical_model", {}).get("path"))
    dbt_project_path = Path(config.get("physical_model", {}).get("path"))

    dbt_parser = DBTParser(dbt_project_path, release["new_model"])

    odm_project = ODMVersionedProjectParser(odm_project_path=odm_project_path)

    PM = dbt_parser.parse_pm()
    odm_project.parse_version(release["new_model"], PM)
    LM = odm_project.get_model(release["new_model"])

    config["data_catalog"]["notion_token"] = environ["NOTION_TOKEN"]
    config["data_catalog"]["dc_table_id"] = environ["DATA_CATALOG_ID"]

    ndc_engine = NotionDataCatalog(
        notion_config=config["data_catalog"],
    )

    DC = DataCatalog(
        engine=ndc_engine,
        config=config,
    )

    DC.sync_with_model(LM)
