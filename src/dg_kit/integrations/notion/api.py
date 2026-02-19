from __future__ import annotations
from typing import Dict, List

from notion_client import Client

from dg_kit.base.data_catalog import DataCatalogEngine
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference,
    IndexedCatalog,
)
from dg_kit.base.enums import (
    DataUnitType,
    DataCatalogRowProperties,
)

from dg_kit.integrations.notion.formater import RowFormater
from dg_kit.integrations.notion.parser import PageParser


class NotionDataCatalog(DataCatalogEngine):
    def __init__(
        self,
        notion_config: dict,
    ):
        self.notion = Client(auth=notion_config["notion_token"])
        self.dc_table_id = notion_config["dc_table_id"]
        self.notion_page_by_id: Dict[str, str] = {}
        self.row_formater = RowFormater(notion_config)
        self.page_parser = PageParser(notion_config)

    def _overwrite_page_body(self, page_id: str, new_blocks: list[dict]) -> None:
        # 1) delete all existing top-level blocks
        for block in self._list_page_blocks(page_id):
            bid = block.get("id")
            if not bid:
                continue
            self.notion.blocks.delete(block_id=bid)

        # 2) append new blocks (<=100 per request) :contentReference[oaicite:3]{index=3}
        for i in range(0, len(new_blocks), 100):
            self.notion.blocks.children.append(
                block_id=page_id, children=new_blocks[i : i + 100]
            )

    def _list_page_blocks(self, page_id: str, page_size=100) -> list[dict]:
        blocks: List[Dict] = []
        cursor: str = None

        while True:
            resp = self.notion.blocks.children.list(
                block_id=page_id, page_size=page_size, start_cursor=cursor
            )
            blocks.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
            if not cursor:
                break

        return blocks

    def _get_references(
        self, index: Dict, notion_page_ids: list[str]
    ) -> ObjectReference:
        return tuple(
            ObjectReference(id=index[notion_page_id], reference_link=notion_page_id)
            for notion_page_id in notion_page_ids
        )

    def pull_data_catalog(self, page_size=100) -> list[DataCatalogRow]:
        print("Pulling data from Notion...")
        rows_by_id: Dict[str, DataCatalogRow] = {}
        page_by_id: Dict[str, EntityPage | AttributePage | RelationPage] = {}
        id_by_notion_page: Dict[str, str] = {}
        raw_page_by_id: Dict[str, dict] = {}
        start_cursor: str = None

        while True:
            payload: dict = {"data_source_id": self.dc_table_id, "page_size": page_size}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = self.notion.data_sources.query(**payload)

            for page in resp["results"]:
                props = page["properties"]
                notion_page_id = page["id"]

                id = self.page_parser.get_property_value(
                    props, DataCatalogRowProperties.ID
                )
                title = self.page_parser.get_property_value(
                    props, DataCatalogRowProperties.TITLE
                )
                domain = self.page_parser.get_property_value(
                    props, DataCatalogRowProperties.DOMAIN
                )
                unit_type = DataUnitType(
                    self.page_parser.get_property_value(
                        props, DataCatalogRowProperties.UNIT_TYPE
                    )
                )

                row = DataCatalogRow(
                    id=id,
                    reference=ObjectReference(id=id, reference_link=page["id"]),
                    data_unit_name=title,
                    data_unit_type=unit_type,
                    domain=domain,
                    last_edited_time=page.get("last_edited_time"),
                    created_time=page.get("created_time"),
                )

                rows_by_id[id] = row

                page_blocks = self._list_page_blocks(notion_page_id)

                # if unit_type == DataUnitType.ENTITY:
                raw_page = self.page_parser.parse_page_from_blocks(
                    unit_type, page_blocks
                )
                raw_page["id"] = id
                raw_page["reference"] = ObjectReference(
                    id=id, reference_link=notion_page_id
                )
                raw_page["data_unit_type"] = unit_type
                raw_page_by_id[id] = raw_page
                id_by_notion_page[notion_page_id] = id
                self.notion_page_by_id[id] = ObjectReference(id, notion_page_id)

            if not resp.get("has_more"):
                break
            start_cursor = resp.get("next_cursor")
            if not start_cursor:
                break

        for id, row in rows_by_id.items():
            raw_page = raw_page_by_id[id]
            unit_type = row.data_unit_type

            if unit_type == DataUnitType.ENTITY:
                page_obj = EntityPage(
                    id=id,
                    reference=raw_page["reference"],
                    data_unit_type=unit_type,
                    description=raw_page["description"],
                    pk_attributes_references=self._get_references(
                        id_by_notion_page, raw_page["pk_attributes_references"]
                    ),
                    attributes_references=self._get_references(
                        id_by_notion_page, raw_page["attributes_references"]
                    ),
                    relations_references=self._get_references(
                        id_by_notion_page, raw_page["relations_references"]
                    ),
                    linked_documents=raw_page["linked_documents"],
                    responsible_parties=raw_page["responsible_parties"],
                    pm_mapping_references=raw_page["pm_mapping_references"],
                    source_systems=raw_page["source_systems"],
                )

            elif unit_type == DataUnitType.ATTRIBUTE:
                page_obj = AttributePage(
                    id=id,
                    reference=raw_page["reference"],
                    data_unit_type=unit_type,
                    description=raw_page["description"],
                    parent_entity_reference=raw_page["parent_entity_reference"],
                    data_type=raw_page["data_type"],
                    sensitivity_type=raw_page["sensitivity_type"],
                    linked_documents=raw_page["linked_documents"],
                    responsible_parties=raw_page["responsible_parties"],
                    pm_mapping_references=raw_page["pm_mapping_references"],
                    source_systems=raw_page["source_systems"],
                )

            elif unit_type == DataUnitType.RELATION:
                page_obj = RelationPage(
                    id=id,
                    reference=raw_page["reference"],
                    data_unit_type=unit_type,
                    description=raw_page["description"],
                    source_entity_reference=raw_page["source_entity_reference"],
                    target_entity_reference=raw_page["target_entity_reference"],
                    linked_documents=raw_page["linked_documents"],
                    responsible_parties=raw_page["responsible_parties"],
                    pm_mapping_references=raw_page["pm_mapping_references"],
                    source_systems=raw_page["source_systems"],
                )
            else:
                raise ValueError(f"Unsupported data unit type: {unit_type}")

            page_by_id[id] = page_obj

            ic = IndexedCatalog(
                row_by_id=rows_by_id,
                reference_by_id=self.notion_page_by_id,
                page_by_id=page_by_id,
            )

        return ic

    def update_page(self, page_obj: EntityPage | AttributePage | RelationPage) -> None:
        if isinstance(page_obj, EntityPage):
            blocks = self.row_formater.build_entity_page_blocks(page_obj)
        elif isinstance(page_obj, AttributePage):
            blocks = self.row_formater.build_attribute_page_blocks(page_obj)
        elif isinstance(page_obj, RelationPage):
            blocks = self.row_formater.build_relation_page_blocks(page_obj)
        else:
            raise ValueError(f"Unsupported data unit type: {page_obj.data_unit_type}")

        self._overwrite_page_body(page_obj.reference.reference_link, blocks)

    def add_page(self, data_unit_page):
        self.update_page(data_unit_page)

    def update_row(self, data_catalog_row: DataCatalogRow) -> None:
        props = self.row_formater.properties_from_row(data_catalog_row)

        self.notion.pages.update(
            page_id=data_catalog_row.reference.reference_link, properties=props
        )

    def add_row(self, data_catalog_row: DataCatalogRow) -> None:
        page = self.notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": self.dc_table_id},
            properties=self.row_formater.properties_from_row(data_catalog_row),
        )

        reference = ObjectReference(data_catalog_row.id, page["id"])

        self.notion_page_by_id[data_catalog_row.id] = reference

        return reference

    def delete_by_id(self, id: str) -> None:
        self.notion.pages.update(page_id=id, archived=True)
