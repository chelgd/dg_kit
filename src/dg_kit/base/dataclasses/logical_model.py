from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple

from dg_kit.base.dataclasses import id_generator
from dg_kit.base.dataclasses.business_information import Team, Document


@dataclass(frozen=True, slots=True)
class EntityIdentifier:
    id: str = field(init=False)
    natural_key: str
    name: Optional[str]
    is_pk: bool
    entity_id: str
    used_attributes_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Relation:
    id: str = field(init=False)
    natural_key: str
    name: str
    domain: Optional[str]
    description: str
    pm_map: Tuple[str, ...]
    master_source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    source_entity_id: str
    target_entity_id: str
    optional_source: Optional[bool]
    optional_target: Optional[bool]
    source_cardinality: Optional[str]
    target_cardinality: Optional[str]
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Attribute:
    id: str = field(init=False)
    natural_key: str
    name: str
    domain: Optional[str]
    description: str
    sensitivity_type: str
    data_type: str
    pm_map: Tuple[str, ...]
    master_source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    entity_id: str
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Entity:
    id: str = field(init=False)
    natural_key: str
    name: str
    domain: Optional[str]
    description: str
    identifiers: Tuple[EntityIdentifier, ...]
    attributes: Tuple[str, ...]
    pm_map: Tuple[str, ...]
    master_source_systems: Tuple[str, ...]
    responsible_parties: Tuple[Team, ...]
    documents: Tuple[Document, ...]
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))
