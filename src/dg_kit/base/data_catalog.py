from __future__ import annotations


from abc import ABC, abstractmethod
from typing import Dict, List

from dg_kit.base.dataclasses.data_catalog import DataCatalogRow

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

    @abstractmethod
    def get_row_by_id(self, id: str) -> DataCatalogRow:
        return self.rows_by_id.get(id)

    @abstractmethod
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
        engine: DataCatalogEngine,
    ):
        self.LM = LM
        self.PM = PM
        self.engine = engine
        self.lm_objects_by_pm_id: Dict[str, List[Entity | Attribute | Relation]] = {}
        self.pm_objects_by_lm_id: Dict[str, List[Layer | Table | Column]] = (
            self.LM.pm_objects_by_lm_id
        )

        for lm_id, pm_obj in self.pm_objects_by_lm_id.items():
            for obj in pm_obj:
                unit_id = obj.id
                if unit_id in self.lm_objects_by_pm_id:
                    self.lm_objects_by_pm_id[unit_id].append(
                        self.LM.all_units_by_id[lm_id]
                    )
                else:
                    self.lm_objects_by_pm_id[unit_id] = [self.LM.all_units_by_id[lm_id]]
