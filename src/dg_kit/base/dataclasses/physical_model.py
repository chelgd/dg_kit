from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Layer:
    id: str
    natural_key: str
    name: str
    is_landing: bool


@dataclass(frozen=True, slots=True)
class Table:
    id: str
    natural_key: str
    layer_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Column:
    id: str
    natural_key: str
    layer_id: str
    table_id: str
    name: str
    data_type: str
    description: str = ""
