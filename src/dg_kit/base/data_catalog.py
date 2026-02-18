from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Tuple
from os import environ
import pickle
from pathlib import Path

from dg_kit.utils.artifact.local import LocalArtifact
from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference,
    IndexedCatalog
)
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.dataclasses.logical_model import (
    Entity,
    Attribute,
    Relation,
)

class DataCatalogEngine(ABC):
    @abstractmethod
    def pull_data_catalog(self) -> Tuple[Dict[str, DataCatalogRow], Dict[str, EntityPage | AttributePage | RelationPage]]:
        raise NotImplementedError

    @abstractmethod
    def update_row(self, data_catalog_row: DataCatalogRow) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_page(
        self, data_unit_page: EntityPage | AttributePage | RelationPage
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_page(self, data_unit_page: EntityPage | AttributePage | RelationPage) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_row(self, data_catalog_row: DataCatalogRow) -> ObjectReference:
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id: str) -> None:
        raise NotImplementedError


class DataCatalog:
    def __init__(
        self,
        engine: DataCatalogEngine,
        config: Dict,
    ):
        self.engine = engine
        self.config = config
        self.artifact_path = Path(f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl")

        if self.artifact_path.exists():
            self.indexed_catalog: IndexedCatalog = self.load_from_local()

        else:
            self.indexed_catalog = self.engine.pull_data_catalog()
            self.save_to_local()


    def get_row_by_id(self, id: str) -> DataCatalogRow:
        return self.indexed_catalog.row_by_id.get(id)

    def get_page_by_id(self, id: str) -> Entity | Attribute | Relation:
        return self.indexed_catalog.page_by_id.get(id)

    def update_row(
        self, data_catalog_row: DataCatalogRow
    ) -> None:
        self.indexed_catalog.row_by_id[data_catalog_row.id] = data_catalog_row
        self.engine.update_row(data_catalog_row)

    def update_page(
        self, page: EntityPage | AttributePage | RelationPage
    ) -> None:
        print(f'Updating page: {page}')
        self.indexed_catalog.page_by_id[page.id] = page
        self.engine.update_page(page)

    def add_page(
        self, page: EntityPage | AttributePage | RelationPage
    ) -> None:
        print(f'Adding page: {page}')
        if page.id in self.indexed_catalog.page_by_id:
            raise KeyError(
                f"Data unit page with id='{page.id}' already exists. Use update instead."
            )
        
        self.indexed_catalog.page_by_id[page.id] = page
        self.engine.add_page(page)

    def add_row(self, data_catalog_row: DataCatalogRow) -> None:
        print(f"Adding new row {data_catalog_row}")
        if data_catalog_row.id in self.indexed_catalog.row_by_id:
            raise KeyError(
                f"Data unit with id='{data_catalog_row.id}' already exists. Use update instead."
            )

        self.indexed_catalog.row_by_id[data_catalog_row.id] = data_catalog_row
        page_reference = self.engine.add_row(data_catalog_row)
        self.indexed_catalog.reference_by_id[data_catalog_row.id] = page_reference

        return page_reference

    def delete_by_id(self, id: str) -> None:
        self.indexed_catalog.row_by_id.pop(id, None)
        self.indexed_catalog.page_by_id.pop(id, None)
        self.engine.delete_by_id(id)

    def sync_with_model(
        self,
        LM: LogicalModel,
    ):
        lm_ids = set(LM.all_units_by_id)
        row_ids = set(self.indexed_catalog.row_by_id)
        rows_and_lm_intersection = row_ids & lm_ids
        rows_diff = row_ids - lm_ids
        lm_diff = lm_ids - row_ids

        for id in rows_diff:
            print(f"Deleting: {id}")
            self.delete_by_id(id)

        print('Adding new rows...')
        for data_unit_id in lm_diff:
            if data_unit_id in LM.entities:
                entity = LM.entities[data_unit_id]
                row = DataCatalogRow(
                    id=entity.id,
                    reference=ObjectReference(
                        id=entity.id,
                        reference_link=self.indexed_catalog.reference_by_id[entity.id].reference_link
                    ),
                    data_unit_name=entity.name,
                    data_unit_type=DataUnitType.ENTITY,
                    domain=entity.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]
                row = DataCatalogRow(
                    id=attribute.id,
                    reference=ObjectReference(
                        id=attribute.id,
                        reference_link=self.indexed_catalog.reference_by_id[attribute.id].reference_link
                    ),
                    data_unit_name=attribute.name,
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    domain=attribute.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]
                row = DataCatalogRow(
                    id=relation.id,
                    reference=ObjectReference(
                        id=relation.id,
                        reference_link=self.indexed_catalog.reference_by_id[relation.id].reference_link
                    ),
                    data_unit_name=relation.name,
                    data_unit_type=DataUnitType.RELATION,
                    domain=relation.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            else:
                print("error")  
                continue

            self.add_row(row)


        print('Adding new pages...')
        for data_unit_id in lm_diff:
            if data_unit_id in LM.entities:       
                entity = LM.entities[data_unit_id]
                
                for identifier in LM.identifiers_by_entity_id[entity.id]:
                    if identifier.is_pk:
                        pk_attributes_references = [
                            self.indexed_catalog.reference_by_id[attribute.id].reference_link for attribute in identifier.attributes
                        ]
                attributes_references = [self.indexed_catalog.reference_by_id[attribute.id].reference_link for attribute in LM.attributes_by_entity_id[entity.id]]
                relations_references = [self.indexed_catalog.reference_by_id[relation.id].reference_link for relation in LM.relations_by_entity_id[entity.id]]

                page = EntityPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[entity.id],
                    data_unit_type=DataUnitType.ENTITY,
                    description=entity.description,
                    pk_attributes_references=pk_attributes_references,
                    attributes_references=attributes_references,
                    relations_references=relations_references,
                    linked_documents=entity.documents,
                    responsible_parties=entity.responsible_parties,
                    pm_mapping_references=entity.pm_map,
                    source_systems=entity.source_systems,
                )
            
            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]

                page = AttributePage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[attribute.id],
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    description=attribute.description,
                    parent_entity_reference=self.indexed_catalog.reference_by_id[attribute.entity_id].reference_link,
                    data_type=attribute.data_type,
                    sensitivity_type=attribute.sensitivity_type,
                    linked_documents=attribute.documents,
                    responsible_parties=attribute.responsible_parties,
                    pm_mapping_references=attribute.pm_map,
                    source_systems=attribute.source_systems,
                )
            
            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]

                page = RelationPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[relation.id],
                    data_unit_type=DataUnitType.RELATION,
                    description=relation.description,
                    source_entity_reference=self.indexed_catalog.reference_by_id[relation.source_entity_id].reference_link,
                    target_entity_reference=self.indexed_catalog.reference_by_id[relation.target_entity_id].reference_link,
                    linked_documents=relation.documents,
                    responsible_parties=relation.responsible_parties,
                    pm_mapping_references=relation.pm_map,
                    source_systems=relation.source_systems,
                )


            else:
                print("error")  
                continue

            self.add_page(page)


        print('Updating rows...')
        for data_unit_id in LM.all_units_by_id:
            if data_unit_id in LM.entities:
                entity = LM.entities[data_unit_id]
                row = DataCatalogRow(
                    id=entity.id,
                    reference=ObjectReference(
                        id=entity.id,
                        reference_link=self.indexed_catalog.reference_by_id[entity.id].reference_link
                    ),
                    data_unit_name=entity.name,
                    data_unit_type=DataUnitType.ENTITY,
                    domain=entity.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )
        
            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]
                row = DataCatalogRow(
                    id=attribute.id,
                    reference=ObjectReference(
                        id=attribute.id,
                        reference_link=self.indexed_catalog.reference_by_id[attribute.id].reference_link
                    ),
                    data_unit_name=attribute.name,
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    domain=attribute.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )
        
            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]
                row = DataCatalogRow(
                    id=relation.id,
                    reference=ObjectReference(
                        id=relation.id,
                        reference_link=self.indexed_catalog.reference_by_id[relation.id].reference_link
                    ),
                    data_unit_name=relation.name,
                    data_unit_type=DataUnitType.RELATION,
                    domain=relation.domain or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )
        
            else:
                print("error")  
                continue
                
            self.update_row(row)


        print('Updating pages...')
        for data_unit_id in rows_and_lm_intersection:
            if data_unit_id in LM.entities:       
                entity = LM.entities[data_unit_id]

                
                for identifier in LM.identifiers_by_entity_id[entity.id]:
                    if identifier.is_pk:
                        pk_attributes_references = [
                            self.indexed_catalog.reference_by_id[attribute.id].reference_link for attribute in identifier.attributes
                        ]
                attributes_references = [self.indexed_catalog.reference_by_id[attribute.id].reference_link for attribute in LM.attributes_by_entity_id[entity.id]]
                relations_references = [self.indexed_catalog.reference_by_id[relation.id].reference_link for relation in LM.relations_by_entity_id[entity.id]]

                page = EntityPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[entity.id],
                    data_unit_type=DataUnitType.ENTITY,
                    description=entity.description,
                    pk_attributes_references=pk_attributes_references,
                    attributes_references=attributes_references,
                    relations_references=relations_references,
                    linked_documents=entity.documents,
                    responsible_parties=entity.responsible_parties,
                    pm_mapping_references=entity.pm_map,
                    source_systems=entity.source_systems,
                )
            
            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]

                page = AttributePage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[attribute.id],
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    description=attribute.description,
                    parent_entity_reference=self.indexed_catalog.reference_by_id[attribute.entity_id].reference_link,
                    data_type=attribute.data_type,
                    sensitivity_type=attribute.sensitivity_type,
                    linked_documents=attribute.documents,
                    responsible_parties=attribute.responsible_parties,
                    pm_mapping_references=attribute.pm_map,
                    source_systems=attribute.source_systems,
                )
            
            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]

                page = RelationPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[relation.id],
                    data_unit_type=DataUnitType.RELATION,
                    description=relation.description,
                    source_entity_reference=self.indexed_catalog.reference_by_id[relation.source_entity_id].reference_link,
                    target_entity_reference=self.indexed_catalog.reference_by_id[relation.target_entity_id].reference_link,
                    linked_documents=relation.documents,
                    responsible_parties=relation.responsible_parties,
                    pm_mapping_references=relation.pm_map,
                    source_systems=relation.source_systems,
                )


            else:
                print("error")  
                continue

            self.update_page(page)
    
    def save_to_local(self):
        with open(f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl", "wb") as f:
            pickle.dump(self.indexed_catalog, f)

    def load_from_local(self):
        with open(f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl", "rb") as f:
            return pickle.load(f)
    