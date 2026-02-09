from __future__ import annotations
from typing import Dict, List


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

        if attribute.entity_id in self.attributes_by_entity_id:
            self.attributes_by_entity_id[attribute.entity_id].append(attribute)
        else:
            self.attributes_by_entity_id[attribute.entity_id] = [attribute]

        for pm_obj in attribute.pm_map:
            if attribute.id in self.pm_objects_by_lm_id:
                self.pm_objects_by_lm_id[attribute.id].append(pm_obj)
            else:
                self.pm_objects_by_lm_id[attribute.id] = [pm_obj]

    def register_relation(self, relation: Relation) -> None:
        self.relations[relation.id] = relation
        self.all_units_by_id[relation.id] = relation

        if relation.source_entity_id in self.relations_by_entity_id:
            self.relations_by_entity_id[relation.source_entity_id].append(relation)
        else:
            self.relations_by_entity_id[relation.source_entity_id] = [relation]

        if relation.target_entity_id in self.relations_by_entity_id:
            self.relations_by_entity_id[relation.target_entity_id].append(relation)
        else:
            self.relations_by_entity_id[relation.target_entity_id] = [relation]

        for pm_obj in relation.pm_map:
            if relation.id in self.pm_objects_by_lm_id:
                self.pm_objects_by_lm_id[relation.id].append(pm_obj)
            else:
                self.pm_objects_by_lm_id[relation.id] = [pm_obj]

    def register_dependency(self, dependent: Entity, dependency: Attribute) -> None:
        if dependent.id in self.dependencies:
            self.dependencies[dependent.id].append(dependency.id)
        else:
            self.dependencies[dependent.id] = [dependency.id]

    def register_identifier(self, identifier: EntityIdentifier) -> None:
        if identifier.entity_id in self.identifiers_by_entity_id:
            self.identifiers_by_entity_id[identifier.entity_id].append(identifier)
        else:
            self.identifiers_by_entity_id[identifier.entity_id] = [identifier]


class LogicalModelsDatabase:
    def __init__(self):
        self.logical_models: Dict[str, LogicalModel] = {}

    def register_logical_model(self, logical_model: LogicalModel) -> None:
        self.logical_models[logical_model.version] = logical_model
