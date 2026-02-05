from __future__ import annotations
from typing import Optional, Dict

from notion_client import Client

from dg_kit.base.data_catalog import DataCatalog
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityTypeDataUnitPageInfo,
    AttributeTypeDataUnitPageInfo,
    RelationTypeDataUnitPageInfo,
)
from dg_kit.integrations.notion.formater import NotionFormater

from dg_kit.base.enums import DataUnitType


class NotionDataCatalog(DataCatalog):
    def __init__(
        self,
        notion_token: str,
        dc_table_id: str,
        prop_title: str = "Data unit",
        prop_type: str = "Data unit type",
        prop_data_unit_uuid: str = "Data unit uuid",
        prop_domain: str = "Domain",
    ):
        self.notion = Client(auth=notion_token)
        self.dc_table_id = dc_table_id
        self.prop_title = prop_title
        self.prop_type = prop_type
        self.prop_domain = prop_domain
        self.prop_data_unit_uuid = prop_data_unit_uuid
        self.rows: list[DataCatalogRow] = []
        self.rows_by_id: Dict[str, DataCatalogRow] = {}
        self.rows_by_name: Dict[str, DataCatalogRow] = {}
        self.rows_by_page_id: Dict[str, DataCatalogRow] = {}
        self.page_id_by_uuid: Dict[str, str] = {}
        self.pull()

    def _properties_from_row(self, row: DataCatalogRow) -> dict:
        props = {
            self.prop_title: {"title": [{"text": {"content": row.data_unit_name}}]},
            self.prop_type: {"select": {"name": row.data_unit_type.value}},
            self.prop_domain: {"select": {"name": row.domain}},
            self.prop_data_unit_uuid: {
                "rich_text": [{"type": "text", "text": {"content": row.data_unit_uuid}}]
            },
        }

        return props

    def _list_child_block_ids(self, page_id: str) -> list[str]:
        ids: list[str] = []
        cursor: Optional[str] = None

        while True:
            resp = self.notion.blocks.children.list(
                block_id=page_id, page_size=100, start_cursor=cursor
            )
            for b in resp.get("results", []):
                bid = b.get("id")
                if bid:
                    ids.append(bid)

            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
            if not cursor:
                break

        return ids

    def _overwrite_page_body(self, page_id: str, new_blocks: list[dict]) -> None:
        # 1) delete all existing top-level blocks
        for bid in self._list_child_block_ids(page_id):
            self.notion.blocks.delete(
                block_id=bid
            )  # archives block :contentReference[oaicite:2]{index=2}

        # 2) append new blocks (<=100 per request) :contentReference[oaicite:3]{index=3}
        for i in range(0, len(new_blocks), 100):
            self.notion.blocks.children.append(
                block_id=page_id, children=new_blocks[i : i + 100]
            )

    def _build_entity_page_blocks(
        self, data_unit_details: EntityTypeDataUnitPageInfo
    ) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(NotionFormater._h2("Description:"))
        if data_unit_details.description:
            blocks.append(NotionFormater._para(data_unit_details.description))
        else:
            blocks.append(NotionFormater._para("—"))

        # Identifiers
        blocks.append(NotionFormater._h2("Primary Key attributes:"))
        if data_unit_details.pk_attributes_page_ids:
            for attribute_page_id in data_unit_details.pk_attributes_page_ids:
                blocks.append(
                    NotionFormater._para_rich_text(
                        [NotionFormater._rt_page_mention(attribute_page_id)]
                    )
                )
        else:
            blocks.append(NotionFormater._para("—"))

        # Attributes
        blocks.append(NotionFormater._h2("Attributes:"))
        if data_unit_details.attributes_page_ids:
            for attribute_page_id in data_unit_details.attributes_page_ids:
                blocks.append(
                    NotionFormater._para_rich_text(
                        [NotionFormater._rt_page_mention(attribute_page_id)]
                    )
                )
        else:
            blocks.append(NotionFormater._para("—"))

        # Attributes
        blocks.append(NotionFormater._h2("Relations:"))
        if data_unit_details.relationes_page_ids:
            for relation_page_id in data_unit_details.relationes_page_ids:
                blocks.append(
                    NotionFormater._para_rich_text(
                        [NotionFormater._rt_page_mention(relation_page_id)]
                    )
                )
        else:
            blocks.append(NotionFormater._para("—"))

        # Linked docs
        blocks.append(NotionFormater._h2("Linked docs:"))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = NotionFormater._bullet(
                    [NotionFormater._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(NotionFormater._para("—"))

        # Responsible parties
        blocks.append(NotionFormater._h2("Responsible parties:"))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                party_name = NotionFormater._bullet(
                    [NotionFormater._rt_text(party.name)]
                )

                blocks.append(party_name)

        else:
            blocks.append(NotionFormater._para("—"))

        # Mapping to core layer tables
        blocks.append(NotionFormater._h2("Core layer map:"))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(NotionFormater._para("—"))

        # Master source systems
        blocks.append(NotionFormater._h2("Master source systems:"))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(source_system)])
                )
        else:
            blocks.append(NotionFormater._para("—"))

        return blocks

    def _build_attribute_page_blocks(
        self, data_unit_details: AttributeTypeDataUnitPageInfo
    ) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(NotionFormater._h2("Description:"))
        if data_unit_details.description:
            blocks.append(NotionFormater._para(data_unit_details.description))
        else:
            blocks.append(NotionFormater._para("—"))

        # Entity
        blocks.append(NotionFormater._h2("Parent entity:"))
        if data_unit_details.parent_entity_page_id:
            blocks.append(
                NotionFormater._para_rich_text(
                    [
                        NotionFormater._rt_page_mention(
                            data_unit_details.parent_entity_page_id
                        )
                    ]
                )
            )
        else:
            blocks.append(NotionFormater._para("—"))

        # Identifiers
        blocks.append(NotionFormater._h2("Data type:"))
        if data_unit_details.data_type:
            blocks.append(NotionFormater._para(data_unit_details.data_type))
        else:
            blocks.append(NotionFormater._para("—"))

        # Identifiers
        blocks.append(NotionFormater._h2("Sensetivity type:"))
        if data_unit_details.sensitivity_type:
            blocks.append(NotionFormater._para(data_unit_details.sensitivity_type))
        else:
            blocks.append(NotionFormater._para("—"))

        # Linked docs
        blocks.append(NotionFormater._h2("Linked docs:"))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = NotionFormater._bullet(
                    [NotionFormater._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(NotionFormater._para("—"))

        # Responsible parties
        blocks.append(NotionFormater._h2("Responsible parties:"))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(party.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(NotionFormater._para("—"))

        # Mapping to core layer tables
        blocks.append(NotionFormater._h2("Core layer map:"))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(NotionFormater._para("—"))

        # Master source systems
        blocks.append(NotionFormater._h2("Master source systems:"))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(source_system)])
                )
        else:
            blocks.append(NotionFormater._para("—"))

        return blocks

    def _build_relation_page_blocks(
        self, data_unit_details: RelationTypeDataUnitPageInfo
    ) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(NotionFormater._h2("Description:"))
        if data_unit_details.description:
            blocks.append(NotionFormater._para(data_unit_details.description))
        else:
            blocks.append(NotionFormater._para("—"))

        # Source entity
        blocks.append(NotionFormater._h2("Source entity:"))
        if data_unit_details.source_entity_page_id:
            blocks.append(
                NotionFormater._para_rich_text(
                    [
                        NotionFormater._rt_page_mention(
                            data_unit_details.source_entity_page_id
                        )
                    ]
                )
            )
        else:
            blocks.append(NotionFormater._para("—"))

        # Target entity
        blocks.append(NotionFormater._h2("Target entity:"))
        if data_unit_details.target_entity_page_id:
            blocks.append(
                NotionFormater._para_rich_text(
                    [
                        NotionFormater._rt_page_mention(
                            data_unit_details.target_entity_page_id
                        )
                    ]
                )
            )
        else:
            blocks.append(NotionFormater._para("—"))

        # Linked docs
        blocks.append(NotionFormater._h2("Linked docs:"))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = NotionFormater._bullet(
                    [NotionFormater._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(NotionFormater._para("—"))

        # Responsible parties
        blocks.append(NotionFormater._h2("Responsible parties:"))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(party.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(NotionFormater._para("—"))

        # Mapping to core layer tables
        blocks.append(NotionFormater._h2("Core layer map:"))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(NotionFormater._para("—"))

        # Master source systems
        blocks.append(NotionFormater._h2("Master source systems:"))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    NotionFormater._bullet([NotionFormater._rt_text(source_system)])
                )
        else:
            blocks.append(NotionFormater._para("—"))

        return blocks

    def pull(self, limit: Optional[int] = None) -> list[DataCatalogRow]:
        start_cursor: Optional[str] = None
        fetched = 0

        while True:
            page_size = 100 if limit is None else min(100, max(1, limit - fetched))
            if limit is not None and page_size <= 0:
                break

            payload: dict = {"data_source_id": self.dc_table_id, "page_size": page_size}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = self.notion.data_sources.query(**payload)

            for page in resp["results"]:
                props = page["properties"]

                data_unit_uuid = NotionFormater._safe_rich_text(
                    props.get(self.prop_data_unit_uuid, {})
                )
                title = NotionFormater._safe_title(props.get(self.prop_title, {}))
                domain = NotionFormater._safe_rich_text(props.get(self.prop_domain, {}))
                typ = props[self.prop_type]["select"]["name"]

                row = DataCatalogRow(
                    data_unit_uuid=data_unit_uuid,
                    data_unit_name=title,
                    data_unit_type=DataUnitType(typ),
                    domain=domain,
                    last_edited_time=page.get("last_edited_time"),
                    created_time=page.get("created_time"),
                )

                self.rows.append(row)

                self.rows_by_id[data_unit_uuid] = row
                self.rows_by_name[title] = row
                self.rows_by_page_id[page["id"]] = row
                self.page_id_by_uuid[data_unit_uuid] = page["id"]

            fetched += len(resp.get("results", []))
            if not resp.get("has_more"):
                break
            start_cursor = resp.get("next_cursor")
            if not start_cursor:
                break

        return self.rows

    def get_by_name(self, name: str) -> DataCatalogRow:
        return self.rows_by_name[name]

    def get_by_id(self, id: str) -> DataCatalogRow:
        return self.rows_by_id[id]

    def _get_by_page_id(self, page_id: str) -> DataCatalogRow:
        return self.rows_by_page_id[page_id]

    def update_page_by_uuid(self, uuid: str, data_unit_details: DataCatalogRow) -> None:
        page_id = self.page_id_by_uuid[uuid]

        # 2) Update page body
        if data_unit_details.data_unit_type == DataUnitType.ENTITY:
            blocks = self._build_entity_page_blocks(data_unit_details)
        elif data_unit_details.data_unit_type == DataUnitType.ATTRIBUTE:
            blocks = self._build_attribute_page_blocks(data_unit_details)
        elif data_unit_details.data_unit_type == DataUnitType.RELATION:
            blocks = self._build_relation_page_blocks(data_unit_details)
        else:
            raise ValueError(
                f"Unsupported data unit type: {data_unit_details.data_unit_type}"
            )

        self._overwrite_page_body(page_id, blocks)

    def update_properties_by_uuid(
        self, uuid: str, data_catalog_row: DataCatalogRow
    ) -> None:
        page_id = self.page_id_by_uuid[uuid]

        props = self._properties_from_row(data_catalog_row)
        self.notion.pages.update(page_id=page_id, properties=props)

        self.rows_by_id[data_catalog_row.data_unit_uuid] = data_catalog_row
        self.rows_by_name[data_catalog_row.data_unit_name] = data_catalog_row
        self.rows.append(data_catalog_row)

    def delete_by_id(self, data_unit_uuid: str) -> None:
        # Find page by external id
        resp = self.notion.data_sources.query(
            data_source_id=self.dc_table_id,
            page_size=1,
            filter={
                "property": self.prop_data_unit_uuid,
                "rich_text": {"equals": data_unit_uuid},
            },
        )
        results = resp.get("results", [])
        if not results:
            raise KeyError(f"No row found for data_unit_uuid='{data_unit_uuid}'")
        page_id = results[0]["id"]

        # Delete page
        self.notion.pages.update(page_id=page_id, archived=True)

        self.pull()

    def delete_by_page_id(self, page_id: str) -> None:
        # Delete page
        self.notion.pages.update(page_id=page_id, archived=True)

        self.pull()

    def add_data_unit(self, data_catalog_row: DataCatalogRow) -> None:
        # 1) If already exists -> overwrite instead of creating duplicate
        resp = self.notion.data_sources.query(
            data_source_id=self.dc_table_id,
            page_size=1,
            filter={
                "property": self.prop_data_unit_uuid,
                "rich_text": {"equals": data_catalog_row.data_unit_uuid},
            },
        )
        results = resp.get("results", [])
        if results:
            raise KeyError(
                f"Data unit with id='{data_catalog_row.data_unit_uuid}' already exists. Use update instead."
            )

        # 2) Create the page (properties only)
        page = self.notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": self.dc_table_id},
            properties=self._properties_from_row(data_catalog_row),
        )
        page_id = page["id"]

        # 3) Update in-memory indexes without calling pull() (avoids duplicates from pull())
        self.rows.append(data_catalog_row)
        self.rows_by_id[data_catalog_row.data_unit_uuid] = data_catalog_row
        self.rows_by_name[data_catalog_row.data_unit_name] = data_catalog_row
        self.rows_by_page_id[page_id] = data_catalog_row
        self.page_id_by_uuid[data_catalog_row.data_unit_uuid] = page_id
