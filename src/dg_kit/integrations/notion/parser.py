from __future__ import annotations

from typing import Optional, Tuple, List, Dict

from notion_client import Client

from dg_kit.base.dataclasses.business_information import Document, Team
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference
)
from dg_kit.base.enums import (
    DataUnitType,
    DataCatalogRowProperties,
)


class PageParser:
    def __init__(
        self,
        config: dict,
    ):
        self.config = config
        self.reversed_mapping = {
            v: k for k, v in self.config['section_name_mapping'].items()
        }

    def get_property_value(self, notion_format_properties: dict, property_name: DataCatalogRowProperties) -> Optional[str]:
        prop = notion_format_properties.get(property_name)

        prop_type = prop.get("type")
        if prop_type == "title":
            return prop['title'][0]['text']['content']
        elif prop_type == "rich_text":
            return prop['rich_text'][0]['text']['content']
        elif prop_type == "select":
            return prop['select']['name']
        else:
            return None

    def _get_prop_from_blocks(self, data_unit_type: DataUnitType, property_name: str, blocks: list[dict]) -> dict:
        if data_unit_type == DataUnitType.ENTITY:
            if property_name == 'description':
                # extract description from blocks
                description = ""
                for block in blocks:
                    if block.get("type") == "paragraph":
                        texts = block["paragraph"]["rich_text"]
                        for text in texts:
                            description += text["plain_text"] + "\n"
                return (property_name, description.strip())
            
            elif property_name == 'pk_attributes_references':

                pk_attributes = []
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            pk_attributes.append(rtext["mention"]["page"]["id"])
                return (property_name, tuple(pk_attributes))
            
            elif property_name == 'attributes_references':
                # extract attributes references from blocks
                attributes = []
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            attributes.append(rtext["mention"]["page"]["id"])
                return (property_name, tuple(attributes))
            
            elif property_name == 'relations_references':
                # extract relations references from blocks
                relations = []
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            relations.append(rtext["mention"]["page"]["id"])
                return (property_name, tuple(relations))
            
            elif property_name == 'linked_documents':
                # extract linked documents from blocks
                linked_docs = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            linked_docs.append(text["plain_text"])
                return (property_name, tuple(linked_docs))
            
            elif property_name == 'responsible_parties':
                # extract responsible parties from blocks
                responsible_parties = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            responsible_parties.append(text["plain_text"])
                return (property_name, tuple(responsible_parties))
            
            elif property_name == 'source_systems':
                # extract source systems from blocks
                source_systems = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            source_systems.append(text["plain_text"])
                return (property_name, tuple(source_systems))
            
            elif property_name == 'pm_mapping_references':
                # extract pm mapping references from blocks
                pm_mappings = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            pm_mappings.append(text["plain_text"])
                return (property_name, tuple(pm_mappings))
        
        elif data_unit_type == DataUnitType.ATTRIBUTE:
            if property_name == 'description':
                # extract description from blocks
                description = ""
                for block in blocks:
                    if block.get("type") == "paragraph":
                        texts = block["paragraph"]["rich_text"]
                        for text in texts:
                            description += text["plain_text"] + "\n"
                return (property_name, description.strip())
            
            elif property_name == 'parent_entity_reference':
                parent_entity_id = ""
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            parent_entity_id = rtext["mention"]["page"]["id"]
                return (property_name, parent_entity_id)
            
            elif property_name == 'data_type':
                data_type = ""
                for block in blocks:
                    if block.get("type") == "paragraph":
                        texts = block["paragraph"]["rich_text"]
                        for text in texts:
                            data_type += text["plain_text"] + "\n"
                return (property_name, data_type.strip())
            
            elif property_name == 'sensitivity_type':
                sensitivity_type = ""
                for block in blocks:
                    if block.get("type") == "paragraph":
                        texts = block["paragraph"]["rich_text"]
                        for text in texts:
                            sensitivity_type += text["plain_text"] + "\n"
                return (property_name, sensitivity_type.strip())
            
            elif property_name == 'linked_documents':
                # extract linked documents from blocks
                linked_docs = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            linked_docs.append(text["plain_text"])
                return (property_name, tuple(linked_docs))
            
            elif property_name == 'responsible_parties':
                # extract responsible parties from blocks
                responsible_parties = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            responsible_parties.append(text["plain_text"])
                return (property_name, tuple(responsible_parties))
            
            elif property_name == 'source_systems':
                # extract source systems from blocks
                source_systems = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            source_systems.append(text["plain_text"])
                return (property_name, tuple(source_systems))
            
            elif property_name == 'pm_mapping_references':
                # extract pm mapping references from blocks
                pm_mappings = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            pm_mappings.append(text["plain_text"])
                return (property_name, tuple(pm_mappings))

        elif data_unit_type == DataUnitType.RELATION:
            if property_name == 'description':
                # extract description from blocks
                description = ""
                for block in blocks:
                    if block.get("type") == "paragraph":
                        texts = block["paragraph"]["rich_text"]
                        for text in texts:
                            description += text["plain_text"] + "\n"
                return (property_name, description.strip())
            
            elif property_name == 'source_entity_reference':
                source_entity_id = ""
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            source_entity_id = rtext["mention"]["page"]["id"]
                return (property_name, source_entity_id)
            
            elif property_name == 'target_entity_reference':
                target_entity_id = ""
                for block in blocks:
                    if block["type"] == "paragraph":
                        rtexts = block["paragraph"]["rich_text"]
                        for rtext in rtexts:
                            target_entity_id = rtext["mention"]["page"]["id"]
                return (property_name, target_entity_id)
            
            elif property_name == 'linked_documents':
                # extract linked documents from blocks
                linked_docs = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            linked_docs.append(text["plain_text"])
                return (property_name, tuple(linked_docs))
            
            elif property_name == 'responsible_parties':
                # extract responsible parties from blocks
                responsible_parties = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            responsible_parties.append(text["plain_text"])
                return (property_name, tuple(responsible_parties))

            elif property_name == 'source_systems':
                # extract source systems from blocks
                source_systems = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            source_systems.append(text["plain_text"])
                return (property_name, tuple(source_systems))
            
            elif property_name == 'pm_mapping_references':
                # extract pm mapping references from blocks
                pm_mappings = []
                for block in blocks:
                    if block.get("type") == "bulleted_list_item":
                        texts = block["bulleted_list_item"]["rich_text"]
                        for text in texts:
                            pm_mappings.append(text["plain_text"])
                return (property_name, tuple(pm_mappings))

    def parse_page_from_blocks(
        self,
        data_unit_type: DataUnitType,
        blocks: List[Dict],
    ) -> Dict:
        raw_page = {}

        len_blocks = len(blocks)
        cursor = 0

        current_section = None
        current_section_blocks = []
        for block in blocks:
            btype = block.get("type")
            if btype == "heading_2":
                if current_section_blocks and current_section:
                    prop_key, prop_value = self._get_prop_from_blocks(data_unit_type.value, current_section, current_section_blocks)
                    raw_page[prop_key] = prop_value
                    current_section_blocks = []
                    current_section = self.reversed_mapping[block["heading_2"]["rich_text"][0]['plain_text']]
                else:
                    current_section = self.reversed_mapping[block["heading_2"]["rich_text"][0]['plain_text']]
            
            else:
                current_section_blocks.append(block)

                if cursor == len_blocks - 1:
                    prop_key, prop_value = self._get_prop_from_blocks(data_unit_type.value, current_section, current_section_blocks)
                    raw_page[prop_key] = prop_value

            cursor += 1

        return raw_page
