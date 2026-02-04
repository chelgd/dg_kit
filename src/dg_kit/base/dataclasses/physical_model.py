from dataclasses import dataclass, field
from dg_kit.base.dataclasses import id_generator


@dataclass(frozen=True, slots=True)
class Layer:
    id: str = field(init=False)
    natural_key: str
    name: str
    is_landing: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Table:
    id: str = field(init=False)
    natural_key: str
    layer_id: str
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Column:
    id: str = field(init=False)
    natural_key: str
    layer_id: str
    table_id: str
    name: str
    data_type: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))