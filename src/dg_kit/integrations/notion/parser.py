from __future__ import annotations

from typing import Optional, Tuple

from notion_client import Client

from dg_kit.base.dataclasses.business_information import Document, Team
from dg_kit.base.dataclasses.data_catalog import DataCatalogRow
from dg_kit.base.dataclasses.logical_model import Attribute, Entity, Relation
from dg_kit.base.enums import DataUnitType
from dg_kit.integrations.notion.formater import NotionFormater


class NotionPageParser:
    _PLACEHOLDER_TEXTS = {"вЂ”", "—"}

    def __init__(
        self,
        notion: Client,
        prop_title: str,
        prop_type: str,
        prop_domain: str,
        prop_data_unit_id: str,
    ) -> None:
        self.notion = notion
        self.prop_title = prop_title
        self.prop_type = prop_type
        self.prop_domain = prop_domain
        self.prop_data_unit_id = prop_data_unit_id

    def list_page_blocks(self, page_id: str) -> list[dict]:
        blocks: list[dict] = []
        cursor: Optional[str] = None

        while True:
            resp = self.notion.blocks.children.list(
                block_id=page_id, page_size=100, start_cursor=cursor
            )
            blocks.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
            if not cursor:
                break

        return blocks

    @staticmethod
    def _plain_text(rich_text: list[dict]) -> str:
        return "".join(item.get("plain_text") or "" for item in rich_text or [])

    @staticmethod
    def _normalize_section(text: str) -> str:
        return text.strip().lower().rstrip(":")

    def _extract_sections(self, blocks: list[dict]) -> dict[str, list[dict]]:
        sections: dict[str, list[dict]] = {}
        current: Optional[str] = None

        for block in blocks:
            btype = block.get("type")
            if btype == "heading_2":
                text = self._plain_text(block.get("heading_2", {}).get("rich_text", []))
                key = self._normalize_section(text)
                current = key
                sections.setdefault(key, [])
                continue
            if current:
                sections[current].append(block)

        return sections

    @staticmethod
    def _extract_page_mentions(rich_text: list[dict]) -> list[str]:
        ids: list[str] = []
        for item in rich_text or []:
            if item.get("type") != "mention":
                continue
            mention = item.get("mention") or {}
            page = mention.get("page") or {}
            page_id = page.get("id")
            if page_id:
                ids.append(page_id)
        return ids

    def _extract_text_items(self, blocks: list[dict]) -> list[str]:
        items: list[str] = []
        for block in blocks:
            btype = block.get("type")
            if btype == "paragraph":
                text = self._plain_text(block.get("paragraph", {}).get("rich_text", []))
                if text:
                    items.append(text)
            elif btype == "bulleted_list_item":
                text = self._plain_text(
                    block.get("bulleted_list_item", {}).get("rich_text", [])
                )
                if text:
                    items.append(text)
        return items

    def _extract_documents(self, blocks: list[dict]) -> Tuple[Document, ...]:
        docs: list[Document] = []
        for block in blocks:
            if block.get("type") != "bulleted_list_item":
                continue
            rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
            text = self._plain_text(rich_text)
            if not text or text in self._PLACEHOLDER_TEXTS:
                continue
            url: Optional[str] = None
            for item in rich_text:
                if item.get("type") == "text":
                    url = ((item.get("text") or {}).get("link") or {}).get(
                        "url"
                    ) or item.get("href")
                    if url:
                        break
            docs.append(Document(natural_key=text, name=text, reference=url))
        return tuple(docs)

    def _extract_teams(self, blocks: list[dict]) -> Tuple[Team, ...]:
        teams: list[Team] = []
        for name in self._extract_text_items(blocks):
            if name in self._PLACEHOLDER_TEXTS:
                continue
            teams.append(Team(natural_key=name, name=name, contacts=()))
        return tuple(teams)

    def _get_row_from_page(self, page_id: str) -> tuple[DataCatalogRow, dict]:
        page = self.notion.pages.retrieve(page_id=page_id)
        props = page["properties"]

        data_unit_id = NotionFormater._safe_rich_text(
            props.get(self.prop_data_unit_id, {})
        )
        title = NotionFormater._safe_title(props.get(self.prop_title, {}))
        domain = NotionFormater._safe_rich_text(props.get(self.prop_domain, {}))
        unit_type = DataUnitType(props[self.prop_type]["select"]["name"])

        row = DataCatalogRow(
            id=data_unit_id,
            data_unit_name=title,
            data_unit_type=unit_type,
            domain=domain,
            last_edited_time=page.get("last_edited_time"),
            created_time=page.get("created_time"),
        )
        return row, page

    def _resolve_row_and_page(
        self,
        page_id: str,
        row: Optional[DataCatalogRow],
        page: Optional[dict],
    ) -> tuple[DataCatalogRow, dict]:
        if row is not None and page is not None:
            return row, page
        return self._get_row_from_page(page_id)

    def _normalize_value(self, value: str) -> str:
        if value in self._PLACEHOLDER_TEXTS:
            return ""
        return value

    def parse_entity_from_page(
        self,
        page_id: str,
        row: Optional[DataCatalogRow] = None,
        page: Optional[dict] = None,
    ) -> tuple[DataCatalogRow, Entity]:
        row, page = self._resolve_row_and_page(page_id, row, page)

        blocks = self.list_page_blocks(page_id)
        sections = self._extract_sections(blocks)

        description_items = self._extract_text_items(sections.get("description", []))
        description = (
            self._normalize_value(description_items[0]) if description_items else ""
        )

        documents = self._extract_documents(sections.get("linked docs", []))
        responsible_parties = self._extract_teams(
            sections.get("responsible parties", [])
        )
        core_layer_map = tuple(
            self._extract_text_items(sections.get("core layer map", []))
        )
        source_systems = tuple(
            self._extract_text_items(sections.get("master source systems", []))
        )

        entity = Entity(
            id=row.id,
            name=row.data_unit_name,
            domain=row.domain,
            description=description,
            pm_map=core_layer_map,
            source_systems=source_systems,
            responsible_parties=responsible_parties,
            documents=documents,
            created_by=(page.get("created_by") or {}).get("id"),
            created_time=row.created_time,
        )

        return row, entity

    def parse_attribute_from_page(
        self,
        page_id: str,
        row: Optional[DataCatalogRow] = None,
        page: Optional[dict] = None,
    ) -> tuple[DataCatalogRow, Attribute]:
        row, page = self._resolve_row_and_page(page_id, row, page)

        blocks = self.list_page_blocks(page_id)
        sections = self._extract_sections(blocks)

        description_items = self._extract_text_items(sections.get("description", []))
        description = (
            self._normalize_value(description_items[0]) if description_items else ""
        )

        parent_entity_id: Optional[str] = None
        for block in sections.get("parent entity", []):
            if block.get("type") == "paragraph":
                mentions = self._extract_page_mentions(
                    block.get("paragraph", {}).get("rich_text", [])
                )
                if mentions:
                    parent_entity_id = mentions[0]
                    break

        data_type_items = self._extract_text_items(sections.get("data type", []))
        data_type = self._normalize_value(data_type_items[0]) if data_type_items else ""

        sensitivity_items = self._extract_text_items(
            sections.get("sensetivity type", [])
        )
        sensitivity_type = (
            self._normalize_value(sensitivity_items[0]) if sensitivity_items else ""
        )

        documents = self._extract_documents(sections.get("linked docs", []))
        responsible_parties = self._extract_teams(
            sections.get("responsible parties", [])
        )
        core_layer_map = tuple(
            self._extract_text_items(sections.get("core layer map", []))
        )
        source_systems = tuple(
            self._extract_text_items(sections.get("master source systems", []))
        )

        attribute = Attribute(
            id=row.id,
            entity_id=parent_entity_id or "",
            name=row.data_unit_name,
            domain=row.domain,
            description=description,
            sensitivity_type=sensitivity_type,
            data_type=data_type,
            pm_map=core_layer_map,
            source_systems=source_systems,
            responsible_parties=responsible_parties,
            documents=documents,
            created_by=(page.get("created_by") or {}).get("id"),
            created_time=row.created_time,
        )

        return row, attribute

    def parse_relation_from_page(
        self,
        page_id: str,
        row: Optional[DataCatalogRow] = None,
        page: Optional[dict] = None,
    ) -> tuple[DataCatalogRow, Relation]:
        row, page = self._resolve_row_and_page(page_id, row, page)

        blocks = self.list_page_blocks(page_id)
        sections = self._extract_sections(blocks)

        description_items = self._extract_text_items(sections.get("description", []))
        description = (
            self._normalize_value(description_items[0]) if description_items else ""
        )

        source_entity_id: Optional[str] = None
        for block in sections.get("source entity", []):
            if block.get("type") == "paragraph":
                mentions = self._extract_page_mentions(
                    block.get("paragraph", {}).get("rich_text", [])
                )
                if mentions:
                    source_entity_id = mentions[0]
                    break

        target_entity_id: Optional[str] = None
        for block in sections.get("target entity", []):
            if block.get("type") == "paragraph":
                mentions = self._extract_page_mentions(
                    block.get("paragraph", {}).get("rich_text", [])
                )
                if mentions:
                    target_entity_id = mentions[0]
                    break

        documents = self._extract_documents(sections.get("linked docs", []))
        responsible_parties = self._extract_teams(
            sections.get("responsible parties", [])
        )
        core_layer_map = tuple(
            self._extract_text_items(sections.get("core layer map", []))
        )
        source_systems = tuple(
            self._extract_text_items(sections.get("master source systems", []))
        )

        relation = Relation(
            id=row.id,
            source_entity_id=source_entity_id or "",
            target_entity_id=target_entity_id or "",
            name=row.data_unit_name,
            domain=row.domain,
            description=description,
            pm_map=core_layer_map,
            source_systems=source_systems,
            responsible_parties=responsible_parties,
            documents=documents,
            optional_source=None,
            optional_target=None,
            source_cardinality=None,
            target_cardinality=None,
            created_by=(page.get("created_by") or {}).get("id"),
            created_time=row.created_time,
        )

        return row, relation
