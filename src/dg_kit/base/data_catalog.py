from __future__ import annotations


from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, final

from dg_kit.base import add_value_to_indexed_list
from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference,
)
from dg_kit.base.business_information import BusinessInformation
from dg_kit.base.dataclasses.business_information import (
    Document,
    Team, Contact,
    Email, Url
)
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.dataclasses.logical_model import (
    Entity,
    Attribute,
    Relation,
)
from dg_kit.base.physical_model import PhysicalModel
from dg_kit.base.dataclasses.physical_model import (
    Layer,
    Table,
    Column,
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
        LM: LogicalModel,
        PM: PhysicalModel,
        BI: BusinessInformation,
        engine: DataCatalogEngine,
    ):
        self.LM = LM
        self.PM = PM
        self.BI = BI
        self.engine = engine
        self.lm_objects_by_pm_id: Dict[str, List[Entity | Attribute | Relation]] = {}
        self.bi_objects_by_pm_id: Dict[str, List[Team | Contact | Document | Email | Url]] = {}
        self.pm_objects_by_lm_id: Dict[str, List[Layer | Table | Column]] = self.LM.pm_objects_by_lm_id
        self.bi_objects_by_lm_id: Dict[str, List[Team | Contact | Document | Email | Url]] = {}
        self.lm_objects_by_bi_id: Dict[str, List[Entity | Attribute | Relation]] = {}
        self.pm_objects_by_bi_id: Dict[str, List[Layer | Table | Column]] = {}
        self.rows_by_id: Dict[str, DataCatalogRow] = {}
        self.references_by_id: Dict[str, ObjectReference] = {}
        self.page_by_id: Dict[str, Entity | Attribute | Relation] = {}

        self.rows_by_id, self.page_by_id, self.references_by_id = self.engine.pull_data_catalog()

        # Build lm_objects_by_pm_id
        for lm_id, pm_objs in self.pm_objects_by_lm_id.items():
            for pm_obj in pm_objs:
                add_value_to_indexed_list(
                    self.lm_objects_by_pm_id,
                    pm_obj.id,
                    self.LM.all_units_by_id[lm_id],
                )
        
        self.lm_ids = set(self.LM.all_units_by_id)
        self.row_ids = set(self.rows_by_id)
        self.rows_and_lm_intersection = self.row_ids & self.lm_ids
        self.rows_diff = self.row_ids - self.lm_ids
        self.lm_diff = self.lm_ids - self.row_ids
        ## Build bi_objects_by_lm_id and lm_objects_by_bi_id
        #for lm_id, lm_obj in self.LM.all_units_by_id.items():
        #    linked_bi_units: List[Team | Contact | Document | Email | Url] = []
        #    linked_bi_units.extend(lm_obj.responsible_parties)
        #    linked_bi_units.extend(lm_obj.documents)
        #    for team in lm_obj.responsible_parties:
        #        linked_bi_units.extend(team.contacts)
        #        for contact in team.contacts:
        #            linked_bi_units.extend(contact.emails)
        #            linked_bi_units.extend(contact.urls)
        #    for bi_unit in linked_bi_units:
        #        add_value_to_indexed_list(self.bi_objects_by_lm_id, lm_id, bi_unit)
        #        add_value_to_indexed_list(self.lm_objects_by_bi_id, bi_unit.id, lm_obj)
        #    del linked_bi_units
        #    
        #for bi_id, lm_objs in self.lm_objects_by_bi_id.items():
        #    for lm_obj in lm_objs:
        #        for pm_obj in self.pm_objects_by_lm_id.get(lm_obj.id, []):
        #            add_value_to_indexed_list(self.pm_objects_by_bi_id, bi_id, pm_obj)
        #
        #for pm_id, lm_objs in self.lm_objects_by_pm_id.items():
        #    for lm_obj in lm_objs:
        #        for bi_unit in self.bi_objects_by_lm_id.get(lm_obj.id, []):
        #            add_value_to_indexed_list(self.bi_objects_by_pm_id, pm_id, bi_unit)

    def get_row_by_id(self, id: str) -> DataCatalogRow:
        return self.rows_by_id.get(id)

    def get_page_by_id(self, id: str) -> Entity | Attribute | Relation:
        return self.page_by_id.get(id)

    def update_row(
        self, data_catalog_row: DataCatalogRow
    ) -> None:
        self.rows_by_id[data_catalog_row.id] = data_catalog_row
        self.engine.update_row(data_catalog_row)

    def update_page(
        self, data_unit_page: EntityPage | AttributePage | RelationPage
    ) -> None:
        self.page_by_id[data_unit_page.id] = data_unit_page
        self.engine.update_page(data_unit_page)

    def add_page(
        self, data_unit_page: EntityPage | AttributePage | RelationPage
    ) -> None:
        if data_unit_page.id in self.page_by_id:
            raise KeyError(
                f"Data unit page with id='{data_unit_page.id}' already exists. Use update instead."
            )
        
        self.page_by_id[data_unit_page.id] = data_unit_page
        self.engine.add_page(data_unit_page)

    def add_row(self, data_catalog_row: DataCatalogRow) -> None:
        if data_catalog_row.id in self.rows_by_id:
            raise KeyError(
                f"Data unit with id='{data_catalog_row.id}' already exists. Use update instead."
            )

        self.rows_by_id[data_catalog_row.id] = data_catalog_row
        page_reference = self.engine.add_row(data_catalog_row)
        self.references_by_id[data_catalog_row.id] = page_reference

    def delete_by_id(self, id: str) -> None:
        self.rows_by_id.pop(id, None)
        self.page_by_id.pop(id, None)
        self.engine.delete_by_id(id)
