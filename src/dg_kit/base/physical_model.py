from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional, Sequence, List

from dg_kit.base.dataclasses.physical_model import (
    Table,
    Column,
    Layer,
)


class PhysicalModel:
    def __init__(self, version):
        self.version = version
        self.layers: Mapping[str, Layer] = {}
        self.tables: Mapping[str, Table] = {}
        self.columns: Mapping[str, Column] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.all_units_by_id: Mapping[str, Layer | Table | Column] = {}
        self.all_units_by_natural_key: Mapping[str, Layer | Table | Column] = {}
    
    
    def register_layer(self, layer: Layer):
        self.layers[layer.id] = layer
        self.all_units_by_id[layer.id] = layer
        self.all_units_by_natural_key[layer.natural_key] = layer


    def register_table(self, table: Table) -> None:
        self.tables[table.id] = table
        self.all_units_by_id[table.id] = table
        self.all_units_by_natural_key[table.natural_key] = table


    def register_column(self, column: Column) -> None:
        self.columns[column.id] = column
        self.all_units_by_id[column.id] = column
        self.all_units_by_natural_key[column.natural_key] = column


    def register_dependency(self, dependent: Table, dependency: Table) -> None:
        if dependent.id in self.dependencies:
            self.dependencies[dependent.id].add(dependency.id)
        else:
            self.dependencies[dependent.id] = {dependency.id}