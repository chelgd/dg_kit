from __future__ import annotations
from typing import Optional

from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference
)
from dg_kit.base.dataclasses.logical_model import Attribute, Entity, Relation

class RowFormater:
    def __init__(
        self,
        config: dict,
    ):
        self.config = config

    def properties_from_row(self, row: DataCatalogRow) -> dict:
        props = {
            'data_unit_id': {
                "rich_text": [{"type": "text", "text": {"content": row.id}}]
            },
            'title': {"title": [{"text": {"content": row.data_unit_name}}]},
            'type': {"select": {"name": row.data_unit_type.value}},
            'domain': {"select": {"name": row.domain}},
        }

        return props

    def _rt_text(self, text: str, url: Optional[str] = None) -> dict:
        rt = {"type": "text", "text": {"content": text}}
        if url:
            rt["text"]["link"] = {"url": url}
        return rt

    def _rt_user_mention(self, user_id: str) -> dict:
        return {"type": "mention", "mention": {"user": {"id": user_id}}}

    def _rt_page_mention(self, page_id: str) -> dict:
        return {"type": "mention", "mention": {"page": {"id": page_id}}}

    def _h2(self, text: str) -> dict:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [self._rt_text(text)]},
        }

    def _para(self, text: str) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [self._rt_text(text)]},
        }

    def _para_rich_text(self, rich_text: list[dict]) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_text},
        }

    def _bullet(self, rich_text: list[dict]) -> dict:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rich_text},
        }

    def build_entity_page_blocks(self, data_unit_details: Entity) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if data_unit_details.description:
            blocks.append(self._para(data_unit_details.description))
        else:
            blocks.append(self._para("—"))

        # Identifiers
        blocks.append(self._h2(self.config['section_name_mapping']['pk_attributes_references']))
        if data_unit_details.pk_attributes_references:
            for attribute_ref in data_unit_details.pk_attributes_references:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(attribute_ref)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Attributes
        blocks.append(self._h2(self.config['section_name_mapping']['attributes_references']))
        if data_unit_details.attributes_page_ids:
            for attribute_page_id in data_unit_details.attributes_page_ids:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(attribute_page_id)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Relations
        blocks.append(self._h2(self.config['section_name_mapping']['relations_references']))
        if data_unit_details.relations_page_ids:
            for relation_page_id in data_unit_details.relations_page_ids:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(relation_page_id)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                party_name = self._bullet(
                    [self._rt_text(party.name)]
                )

                blocks.append(party_name)

        else:
            blocks.append(self._para("—"))

        # Master source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        # Mapping to physical model
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    self._bullet([self._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        return blocks

    def build_attribute_page_blocks(self, data_unit_details: Attribute) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if data_unit_details.description:
            blocks.append(self._para(data_unit_details.description))
        else:
            blocks.append(self._para("—"))

        # Entity
        blocks.append(self._h2(self.config['section_name_mapping']['parent_entity_reference']))
        if data_unit_details.parent_entity_page_id:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            data_unit_details.parent_entity_page_id
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Data Type
        blocks.append(self._h2(self.config['section_name_mapping']['data_type']))
        if data_unit_details.data_type:
            blocks.append(self._para(data_unit_details.data_type))
        else:
            blocks.append(self._para("—"))

        # Sensetivity Type
        blocks.append(self._h2(self.config['section_name_mapping']['sensitivity_type']))
        if data_unit_details.sensitivity_type:
            blocks.append(self._para(data_unit_details.sensitivity_type))
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                blocks.append(
                    self._bullet([self._rt_text(party.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Mapping to core layer tables
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    self._bullet([self._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Master source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        return blocks

    def build_relation_page_blocks(self, data_unit_details: Relation) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if data_unit_details.description:
            blocks.append(self._para(data_unit_details.description))
        else:
            blocks.append(self._para("—"))

        # Source entity
        blocks.append(self._h2(self.config['section_name_mapping']['source_entity_reference']))
        if data_unit_details.source_entity_page_reference:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            data_unit_details.source_entity_page_reference
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Target entity
        blocks.append(self._h2(self.config['section_name_mapping']['target_entity_reference']))
        if data_unit_details.target_entity_page_referenc:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            data_unit_details.target_entity_page_referenc
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if data_unit_details.linked_documents:
            for document in data_unit_details.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if data_unit_details.responsible_parties:
            for party in data_unit_details.responsible_parties:
                blocks.append(
                    self._bullet([self._rt_text(party.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Mapping to core layer tables
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if data_unit_details.core_layer_mapping:
            for table in sorted(data_unit_details.core_layer_mapping):
                blocks.append(
                    self._bullet([self._rt_text(table)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Master source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if data_unit_details.master_source_systems:
            for source_system in sorted(data_unit_details.master_source_systems):
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        return blocks
