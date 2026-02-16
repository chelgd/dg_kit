from __future__ import annotations
from typing import Dict, List

from dg_kit.base import add_value_to_indexed_list
from dg_kit.base.dataclasses.logical_model import (
    EntityIdentifier,
    Entity,
    Attribute,
    Relation,
)


class LogicalModel:
    def __init__(self, version: str):
        self.version = version
        self.entities: Dict[str, Entity] = {}
        self.attributes: Dict[str, Attribute] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.relations: Dict[str, Relation] = {}
        self.all_units_by_id: Dict[str, Entity | Attribute | Relation] = {}
        self.relations_by_entity_id: Dict[str, List[Relation]] = {}
        self.attributes_by_entity_id: Dict[str, List[Attribute]] = {}
        self.identifiers_by_entity_id: Dict[str, List[EntityIdentifier]] = {}
        self.pm_objects_by_lm_id: Dict[str, List[str]] = {}

    def register_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        self.all_units_by_id[entity.id] = entity

        for pm_obj in entity.pm_map:
            if entity.id in self.pm_objects_by_lm_id:
                self.pm_objects_by_lm_id[entity.id].append(pm_obj)
            else:
                self.pm_objects_by_lm_id[entity.id] = [pm_obj]

    def register_attribute(self, attribute: Attribute) -> None:
        self.attributes[attribute.id] = attribute
        self.all_units_by_id[attribute.id] = attribute

        add_value_to_indexed_list(self.attributes_by_entity_id, attribute.entity_id, attribute)
        
        for pm_obj in attribute.pm_map:
            add_value_to_indexed_list(self.pm_objects_by_lm_id, attribute.id, pm_obj)
        
    def register_relation(self, relation: Relation) -> None:
        self.relations[relation.id] = relation
        self.all_units_by_id[relation.id] = relation

        add_value_to_indexed_list(self.relations_by_entity_id, relation.source_entity_id, relation)
        add_value_to_indexed_list(self.relations_by_entity_id, relation.target_entity_id, relation)

        for pm_obj in relation.pm_map:
            add_value_to_indexed_list(self.pm_objects_by_lm_id, relation.id, pm_obj)

    def register_dependency(self, dependent: Entity, dependency: Attribute) -> None:
        add_value_to_indexed_list(self.dependencies, dependent.id, dependency.id)

    def register_identifier(self, identifier: EntityIdentifier) -> None:
        add_value_to_indexed_list(self.identifiers_by_entity_id, identifier.entity_id, identifier)


class LogicalModelsDatabase:
    def __init__(self):
        self.logical_models: Dict[str, LogicalModel] = {}

    def register_logical_model(self, logical_model: LogicalModel) -> None:
        self.logical_models[logical_model.version] = logical_model
