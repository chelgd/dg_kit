from __future__ import annotations

from typing import Optional, Tuple

from datetime import datetime

from dataclasses import dataclass

from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.business_information import Document, Team


@dataclass(frozen=True, slots=True)
class DataCatalogRow:
    data_unit_name: str
    data_unit_type: DataUnitType
    domain: str
    data_unit_uuid: str
    last_edited_time: Optional[datetime] = None
    created_time: Optional[datetime] = None

    def __post_init__(self) -> None: ...


@dataclass(frozen=True, slots=True)
class EntityTypeDataUnitPageInfo:
    data_unit_type: DataUnitType
    description: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    master_source_systems: Tuple[str, ...]
    core_layer_mapping: Tuple[str, ...]
    pk_attributes_page_ids: Tuple[str, ...]
    attributes_page_ids: Tuple[str, ...]
    relationes_page_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttributeTypeDataUnitPageInfo:
    parent_entity_page_id: str
    data_unit_type: DataUnitType
    description: str
    data_type: str
    sensitivity_type: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    core_layer_mapping: Tuple[str, ...]
    master_source_systems: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationTypeDataUnitPageInfo:
    data_unit_type: DataUnitType
    description: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    core_layer_mapping: Tuple[str, ...]
    master_source_systems: Tuple[str, ...]
    source_entity_page_id: str
    target_entity_page_id: str
    optional_source: bool
    optional_target: bool
    source_cardinality: str
    target_cardinality: str
