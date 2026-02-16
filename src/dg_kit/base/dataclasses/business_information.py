"""
Docstring for dg_kit.base.dataclasses.business_information
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True, slots=True)
class SlackChannelUrl:
    id: str
    nk: str
    name: str
    url: Optional[str]


@dataclass(frozen=True, slots=True)
class Email:
    id: str
    nk: str
    name: str
    email_address: Optional[str]


@dataclass(frozen=True, slots=True)
class Url:
    id: str
    nk: str
    name: str
    url: Optional[str]


@dataclass(frozen=True, slots=True)
class Contact:
    id: str
    nk: str
    name: str
    emails: Tuple[Email, ...]
    urls: Tuple[Url, ...]


@dataclass(frozen=True, slots=True)
class Team:
    id: str
    nk: str
    name: str
    contacts: Tuple[Contact, ...]


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    nk: str
    name: str
    reference: Optional[str]
