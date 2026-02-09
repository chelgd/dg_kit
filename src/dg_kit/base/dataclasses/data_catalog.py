from __future__ import annotations

from typing import Optional, Tuple

from datetime import datetime

from dataclasses import dataclass

from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.business_information import Document, Team


@dataclass(frozen=True, slots=True)
class DataCatalogRow:
    id: str
    data_unit_name: str
    data_unit_type: DataUnitType
    domain: str
    last_edited_time: Optional[datetime] = None
    created_time: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class EntityPage:
    id: str
    data_unit_type: DataUnitType
    description: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    source_systems: Tuple[str, ...]
    pm_mapping: Tuple[str, ...]
    pk_attributes_references: Tuple[str, ...]
    attributes_references: Tuple[str, ...]
    relations_references: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttributePage:
    id: str
    parent_entity_page_id: str
    data_unit_type: DataUnitType
    description: str
    data_type: str
    sensitivity_type: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    pm_mapping: Tuple[str, ...]
    source_systems: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationPage:
    id: str
    data_unit_type: DataUnitType
    description: str
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    pm_mapping: Tuple[str, ...]
    source_systems: Tuple[str, ...]
    source_entity_page_id: str
    target_entity_page_id: str
    optional_source: bool
    optional_target: bool
    source_cardinality: str
    target_cardinality: str
