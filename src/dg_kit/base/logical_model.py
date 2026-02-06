from __future__ import annotations
from typing import Dict, List


from dg_kit.base.dataclasses.logical_model import EntityIdentifier, Entity, Attribute, Relation


class LogicalModel:
    def __init__(self, version: str):
        self.version = version
        self.entities: Dict[str, Entity] = {}
        self.attributes: Dict[str, Attribute] = {}
        self.dependencies: dict[str, List[str]] = {}
        self.relations: Dict[str, Relation] = {}
        self.all_units_by_id: Dict[str, Entity | Attribute | Relation] = {}
        self.all_units_by_natural_key: Dict[str, Entity | Attribute | Relation] = {}
        self.relations_by_entity_id: Dict[str, List[Relation]] = {}
        self.attributes_by_entity_id: Dict[str, List[Attribute]] = {}
        self.identifiers_by_entity_id: Dict[str, List[EntityIdentifier]] = {}
        self.pm_objects_by_nk: dict[str, List[str]] = {}

    def register_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        self.all_units_by_id[entity.id] = entity
        self.all_units_by_natural_key[entity.natural_key] = entity

        for nk in entity.pm_map:
            if nk in self.pm_objects_by_nk:
                self.pm_objects_by_nk[nk].append(entity.id)
            else:
                self.pm_objects_by_nk[nk] = [entity.id]

    def register_attribute(self, attribute: Attribute) -> None:
        self.attributes[attribute.id] = attribute
        self.all_units_by_id[attribute.id] = attribute
        self.all_units_by_natural_key[attribute.natural_key] = attribute

        if attribute.entity_id in self.attributes_by_entity_id:
            self.attributes_by_entity_id[attribute.entity_id].append(attribute)
        else:
            self.attributes_by_entity_id[attribute.entity_id] = [attribute]

        for nk in attribute.pm_map:
            if nk in self.pm_objects_by_nk:
                self.pm_objects_by_nk[nk].append(attribute.id)
            else:
                self.pm_objects_by_nk[nk] = [attribute.id]

    def register_relation(self, relation: Relation) -> None:
        self.relations[relation.id] = relation
        self.all_units_by_id[relation.id] = relation
        self.all_units_by_natural_key[relation.natural_key] = relation
        if relation.source_entity_id in self.relations_by_entity_id:
            self.relations_by_entity_id[relation.source_entity_id].append(relation)
        else:
            self.relations_by_entity_id[relation.source_entity_id] = [relation]

        if relation.target_entity_id in self.relations_by_entity_id:
            self.relations_by_entity_id[relation.target_entity_id].append(relation)
        else:
            self.relations_by_entity_id[relation.target_entity_id] = [relation]

        for nk in relation.pm_map:
            if nk in self.pm_objects_by_nk:
                self.pm_objects_by_nk[nk].append(relation.id)
            else:
                self.pm_objects_by_nk[nk] = [relation.id]

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
