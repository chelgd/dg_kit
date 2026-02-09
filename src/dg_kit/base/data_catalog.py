from __future__ import annotations


from abc import ABC, abstractmethod
from typing import Dict, List, final

from dg_kit.base.dataclasses.data_catalog import DataCatalogRow

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
    def __init__(
        self,
    ):
        self.rows_by_id: Dict[str, DataCatalogRow] = {}
        self.page_by_id: Dict[str, Entity | Attribute | Relation] = {}

    @abstractmethod
    def pull_data_catalog(self) -> None:
        raise NotImplementedError

    @final
    def get_row_by_id(self, id: str) -> DataCatalogRow:
        return self.rows_by_id.get(id)

    @final
    def get_page_by_id(self, id: str) -> Entity | Attribute | Relation:
        return self.page_by_id.get(id)

    @abstractmethod
    def update_row_by_id(self, id: str, data_catalog_row: DataCatalogRow) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_page_by_id(
        self, id: str, data_unit_page: Entity | Attribute | Relation
    ) -> None:
        self.page_by_id[id] = data_unit_page
        self.engine.update_page_by_id(id, data_unit_page)

    @abstractmethod
    def add_row(self, data_catalog_row: DataCatalogRow) -> None:
        self.rows_by_id[data_catalog_row.id] = data_catalog_row
        self.engine.add_row(data_catalog_row)

    @abstractmethod
    def delete_by_id(self, id: str) -> None:
        self.rows_by_id.pop(id, None)
        self.page_by_id.pop(id, None)


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

        def _add_index(index: Dict[str, List], key: str, value) -> None:
            if key in index:
                if value not in index[key]:
                    index[key].append(value)
            else:
                index[key] = [value]

        # Build lm_objects_by_pm_id
        for lm_id, pm_objs in self.pm_objects_by_lm_id.items():
            for pm_obj in pm_objs:
                _add_index(
                    self.lm_objects_by_pm_id,
                    pm_obj.id,
                    self.LM.all_units_by_id[lm_id],
                )

        # Build bi_objects_by_lm_id and lm_objects_by_bi_id
        for lm_id, lm_obj in self.LM.all_units_by_id.items():
            linked_bi_units: List[Team | Contact | Document | Email | Url] = []

            linked_bi_units.extend(lm_obj.responsible_parties)
            linked_bi_units.extend(lm_obj.documents)

            for team in lm_obj.responsible_parties:
                linked_bi_units.extend(team.contacts)
                for contact in team.contacts:
                    linked_bi_units.extend(contact.emails)
                    linked_bi_units.extend(contact.urls)

            for bi_unit in linked_bi_units:
                _add_index(self.bi_objects_by_lm_id, lm_id, bi_unit)
                _add_index(self.lm_objects_by_bi_id, bi_unit.id, lm_obj)

        for bi_id, lm_objs in self.lm_objects_by_bi_id.items():
            for lm_obj in lm_objs:
                for pm_obj in self.pm_objects_by_lm_id.get(lm_obj.id, []):
                    _add_index(self.pm_objects_by_bi_id, bi_id, pm_obj)

        for pm_id, lm_objs in self.lm_objects_by_pm_id.items():
            for lm_obj in lm_objs:
                for bi_unit in self.bi_objects_by_lm_id.get(lm_obj.id, []):
                    _add_index(self.bi_objects_by_pm_id, pm_id, bi_unit)
