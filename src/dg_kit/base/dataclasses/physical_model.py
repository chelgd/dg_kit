from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Layer:
    id: str
    nk: str
    name: str
    is_landing: bool


@dataclass(frozen=True, slots=True)
class Table:
    id: str
    nk: str
    layer_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Column:
    id: str
    nk: str
    layer_id: str
    table_id: str
    name: str
    data_type: str
    description: str = ""
