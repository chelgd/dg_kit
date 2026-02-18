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
            self.config['row_property_mapping']['id']: {
                "rich_text": [{"type": "text", "text": {"content": row.id}}]
            },
            self.config['row_property_mapping']['title']: {"title": [{"text": {"content": row.data_unit_name}}]},
            self.config['row_property_mapping']['type']: {"select": {"name": row.data_unit_type.value}},
            self.config['row_property_mapping']['domain']: {"select": {"name": row.domain}},
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

    def build_entity_page_blocks(self, entity_page: EntityPage) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if entity_page.description:
            blocks.append(self._para(entity_page.description))
        else:
            blocks.append(self._para("—"))

        # Identifiers
        blocks.append(self._h2(self.config['section_name_mapping']['pk_attributes_references']))
        if entity_page.pk_attributes_references:
            for attribute_ref in entity_page.pk_attributes_references:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(attribute_ref)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Attributes
        blocks.append(self._h2(self.config['section_name_mapping']['attributes_references']))
        if entity_page.attributes_references:
            for attribute_page_id in entity_page.attributes_references:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(attribute_page_id)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Relations
        blocks.append(self._h2(self.config['section_name_mapping']['relations_references']))
        if entity_page.relations_references:
            for relation_page_id in entity_page.relations_references:
                blocks.append(
                    self._para_rich_text(
                        [self._rt_page_mention(relation_page_id)]
                    )
                )
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if entity_page.linked_documents:
            for document in entity_page.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if entity_page.responsible_parties:
            for party in entity_page.responsible_parties:
                party_name = self._bullet(
                    [self._rt_text(party.name)]
                )

                blocks.append(party_name)

        else:
            blocks.append(self._para("—"))

        # Mapping to physical model
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if entity_page.pm_mapping_references:
            for pm_obj_reference in entity_page.pm_mapping_references:
                blocks.append(
                    self._bullet([self._rt_text(pm_obj_reference.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if entity_page.source_systems:
            for source_system in entity_page.source_systems:
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        return blocks

    def build_attribute_page_blocks(self, attribute_page: AttributePage) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if attribute_page.description:
            blocks.append(self._para(attribute_page.description))
        else:
            blocks.append(self._para("—"))

        # Entity
        blocks.append(self._h2(self.config['section_name_mapping']['parent_entity_reference']))
        if attribute_page.parent_entity_reference:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            attribute_page.parent_entity_reference
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Data Type
        blocks.append(self._h2(self.config['section_name_mapping']['data_type']))
        if attribute_page.data_type:
            blocks.append(self._para(attribute_page.data_type))
        else:
            blocks.append(self._para("—"))

        # Sensetivity Type
        blocks.append(self._h2(self.config['section_name_mapping']['sensitivity_type']))
        if attribute_page.sensitivity_type:
            blocks.append(self._para(attribute_page.sensitivity_type))
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if attribute_page.linked_documents:
            for document in attribute_page.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if attribute_page.responsible_parties:
            for party in attribute_page.responsible_parties:
                blocks.append(
                    self._bullet([self._rt_text(party.name)])
                )
        else:
            blocks.append(self._para("—"))

        # Mapping to Physical Model layer tables
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if attribute_page.pm_mapping_references:
            for pm_obj_reference in attribute_page.pm_mapping_references:
                blocks.append(
                    self._bullet([self._rt_text(pm_obj_reference.name)])
                )
        else:
            blocks.append(self._para("—"))

        # Source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if attribute_page.source_systems:
            for source_system in attribute_page.source_systems:
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        return blocks

    def build_relation_page_blocks(self, relation_page: RelationPage) -> list[dict]:
        # Build blocks (example)
        blocks: list[dict] = []

        # Description
        blocks.append(self._h2(self.config['section_name_mapping']['description']))
        if relation_page.description:
            blocks.append(self._para(relation_page.description))
        else:
            blocks.append(self._para("—"))

        # Source entity
        blocks.append(self._h2(self.config['section_name_mapping']['source_entity_reference']))
        if relation_page.source_entity_reference:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            relation_page.source_entity_reference
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Target entity
        blocks.append(self._h2(self.config['section_name_mapping']['target_entity_reference']))
        if relation_page.target_entity_reference:
            blocks.append(
                self._para_rich_text(
                    [
                        self._rt_page_mention(
                            relation_page.target_entity_reference
                        )
                    ]
                )
            )
        else:
            blocks.append(self._para("—"))

        # Linked docs
        blocks.append(self._h2(self.config['section_name_mapping']['linked_documents']))
        if relation_page.linked_documents:
            for document in relation_page.linked_documents:
                document_link = self._bullet(
                    [self._rt_text(document.name, url=document.reference)]
                )
                blocks.append(document_link)
        else:
            blocks.append(self._para("—"))

        # Responsible parties
        blocks.append(self._h2(self.config['section_name_mapping']['responsible_parties']))
        if relation_page.responsible_parties:
            for party in relation_page.responsible_parties:
                blocks.append(
                    self._bullet([self._rt_text(party.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Mapping to core layer tables
        blocks.append(self._h2(self.config['section_name_mapping']['pm_mapping_references']))
        if relation_page.pm_mapping_references:
            for pm_obj_reference in relation_page.pm_mapping_references:
                blocks.append(
                    self._bullet([self._rt_text(pm_obj_reference.name)])
                )  # or _rt_user_mention(not_user_id)
        else:
            blocks.append(self._para("—"))

        # Master source systems
        blocks.append(self._h2(self.config['section_name_mapping']['source_systems']))
        if relation_page.source_systems:
            for source_system in relation_page.source_systems:
                blocks.append(
                    self._bullet([self._rt_text(source_system)])
                )
        else:
            blocks.append(self._para("—"))

        return blocks
