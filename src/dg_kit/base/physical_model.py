from __future__ import annotations

from typing import Dict, List

from dg_kit.base import add_value_to_indexed_list
from dg_kit.base.dataclasses.physical_model import (
    Table,
    Column,
    Layer,
)


class PhysicalModel:
    def __init__(self, version):
        self.version = version
        self.layers: Dict[str, Layer] = {}
        self.tables: Dict[str, Table] = {}
        self.columns: Dict[str, Column] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.all_units_by_id: Dict[str, Layer | Table | Column] = {}

    def register_layer(self, layer: Layer):
        self.layers[layer.id] = layer
        self.all_units_by_id[layer.id] = layer

    def register_table(self, table: Table) -> None:
        self.tables[table.id] = table
        self.all_units_by_id[table.id] = table

    def register_column(self, column: Column) -> None:
        self.columns[column.id] = column
        self.all_units_by_id[column.id] = column

    def register_dependency(self, dependent: Table, dependency: Table) -> None:
        add_value_to_indexed_list(self.dependencies, dependent.id, dependency.id)


class PhysicalModelsDatabase:
    def __init__(self):
        self.physical_models: Dict[str, PhysicalModel] = {}

    def register_physical_model(self, physical_model: PhysicalModel) -> None:
        self.physical_models[physical_model.version] = physical_model
