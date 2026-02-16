from __future__ import annotations

from typing import Optional, Tuple

from datetime import datetime

from dataclasses import dataclass

from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.business_information import Document, Team


@dataclass(frozen=True, slots=True)
class ObjectReference:
    id: str
    reference_link: str


@dataclass(frozen=True, slots=True)
class DataCatalogRow:
    id: str
    data_unit_type: DataUnitType
    data_unit_name: str
    domain: str
    last_edited_time: Optional[datetime] = None
    created_time: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class EntityPage:
    id: str
    reference: ObjectReference
    data_unit_type: DataUnitType
    description: str
    pk_attributes_references: Tuple[ObjectReference, ...]
    attributes_references: Tuple[ObjectReference, ...]
    relations_references: Tuple[ObjectReference, ...]
    linked_documents: Tuple[ObjectReference, ...]
    responsible_parties: Tuple[Team, ...]
    pm_mapping_references: Tuple[ObjectReference, ...]
    source_systems: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttributePage:
    id: str
    reference: ObjectReference
    data_unit_type: DataUnitType
    description: str
    parent_entity_reference: str
    data_type: str
    sensitivity_type: str
    linked_documents: Tuple[ObjectReference, ...]
    responsible_parties: Tuple[Team, ...]
    pm_mapping_references: Tuple[ObjectReference, ...]
    source_systems: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationPage:
    id: str
    reference: ObjectReference
    data_unit_type: DataUnitType
    description: str
    source_entity_reference: ObjectReference
    target_entity_reference: ObjectReference
    linked_documents: Tuple[Document, ...]
    responsible_parties: Tuple[Team, ...]
    pm_mapping_references: Tuple[str, ...]
    source_systems: Tuple[str, ...]
    #optional_source: bool
    #optional_target: bool
    #source_cardinality: str
    #target_cardinality: str
