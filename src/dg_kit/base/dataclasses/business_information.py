"""
Docstring for dg_kit.base.dataclasses.business_information
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from dg_kit.base.dataclasses import id_generator


@dataclass(frozen=True, slots=True)
class SlackChannelUrl:
    id: str = field(init=False)
    natural_key: str
    name: str
    url: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Email:
    id: str = field(init=False)
    natural_key: str
    name: str
    email_address: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Url:
    id: str = field(init=False)
    natural_key: str
    name: str
    url: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Contact:
    id: str = field(init=False)
    natural_key: str
    name: str
    emails: Tuple[Email, ...]
    urls: Tuple[Url, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Team:
    id: str = field(init=False)
    natural_key: str
    name: str
    contacts: Tuple[Contact, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))


@dataclass(frozen=True, slots=True)
class Document:
    id: str = field(init=False)
    natural_key: str
    name: str
    reference: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", id_generator(self.natural_key))
