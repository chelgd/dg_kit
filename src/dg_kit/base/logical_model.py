from __future__ import annotations
from typing import Mapping, List


from dg_kit.base.dataclasses.logical_model import Entity, Attribute, Relation


class LogicalModel:
    def __init__(self, version: str):
        self.version = version
        self.entities: Mapping[str, Entity] = {}
        self.attributes: Mapping[str, Attribute] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.relations: Mapping[str, Relation] = {}
        self.relations_ids_by_entity_id: Mapping[str, List[Relation]] = {}
        self.all_units_by_id: Mapping[str, Entity | Attribute | Relation] = {}
        self.all_units_by_natural_key: Mapping[str, Entity | Attribute | Relation] = {}
        self.pm_objects_nks_used: set = set()

    def register_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        self.all_units_by_id[entity.id] = entity
        self.all_units_by_natural_key[entity.natural_key] = entity

        for nk in entity.pm_map:
            self.pm_objects_nks_used.add(nk)

    def register_attribute(self, attribute: Attribute) -> None:
        self.attributes[attribute.id] = attribute
        self.all_units_by_id[attribute.id] = attribute
        self.all_units_by_natural_key[attribute.natural_key] = attribute

        for nk in attribute.pm_map:
            self.pm_objects_nks_used.add(nk)

    def register_relation(self, relation: Relation) -> None:
        self.relations[relation.id] = relation
        self.all_units_by_id[relation.id] = relation
        self.all_units_by_natural_key[relation.natural_key] = relation
        if relation.source_entity_id in self.relations_ids_by_entity_id:
            self.relations_ids_by_entity_id[relation.source_entity_id].append(relation)
        else:
            self.relations_ids_by_entity_id[relation.source_entity_id] = [relation]

        if relation.target_entity_id in self.relations_ids_by_entity_id:
            self.relations_ids_by_entity_id[relation.target_entity_id].append(relation)
        else:
            self.relations_ids_by_entity_id[relation.target_entity_id] = [relation]

        for nk in relation.pm_map:
            self.pm_objects_nks_used.add(nk)

    def register_dependency(self, dependent: Entity, dependency: Attribute) -> None:
        if dependent.id in self.dependencies:
            self.dependencies[dependent.id].add(dependency.id)
        else:
            self.dependencies[dependent.id] = {dependency.id}


class LogicalModelsDatabase:
    def __init__(self):
        self.logical_models: Mapping[str, LogicalModel] = {}

    def register_logical_model(self, logical_model: LogicalModel) -> None:
        self.logical_models[logical_model.version] = logical_model
