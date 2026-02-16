from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from dg_kit.base.dataclasses.business_information import Team, Document
from dg_kit.base.dataclasses.physical_model import Column, Table


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    nk: str
    name: str
    domain: Optional[str]
    description: str
    pm_map: Tuple[str, Table | Column]
    source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Attribute:
    id: str
    nk: str
    entity_id: str
    name: str
    domain: Optional[str]
    description: str
    sensitivity_type: str
    data_type: str
    pm_map: Tuple[str, Column]
    source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class EntityIdentifier:
    id: str
    nk: str
    entity_id: str
    name: Optional[str]
    is_pk: bool
    attributes: Tuple[Attribute, ...]


@dataclass(frozen=True, slots=True)
class Relation:
    id: str
    nk: str
    source_entity_id: str
    target_entity_id: str
    name: str
    domain: Optional[str]
    description: str
    pm_map: Tuple[str, Table | Column]
    source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    optional_source: Optional[bool]
    optional_target: Optional[bool]
    source_cardinality: Optional[str]
    target_cardinality: Optional[str]
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None
