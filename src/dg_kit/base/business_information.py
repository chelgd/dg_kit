from __future__ import annotations
from typing import Any, Mapping, Dict


from dg_kit.base.dataclasses.business_information import (
    Team,
    Contact,
    Document,
    Email,
    Url
)


class BusinessInformation:
    def __init__(self, version: str):
        self.version = version
        self.teams: Mapping[str, Team] = {}
        self.contacts: Mapping[str, Contact] = {}
        self.documents: Mapping[str, Document] = {}
        self.emails: Mapping[str, Email] = {}
        self.urls: Mapping[str, Url] = {}
        self.all_units_by_id: Mapping[str, Team | Contact | Document | Email | Url] = {}
        self.all_units_by_natural_key: Mapping[str, Team | Contact | Document | Email | Url] = {}

    def register_team(self, team: Team) -> None:
        self.teams[team.id] = team
        self.all_units_by_id[team.id] = team
        self.all_units_by_natural_key[team.natural_key] = team
    
    def register_contact(self, contact: Contact) -> None:
        self.contacts[contact.id] = contact
        self.all_units_by_id[contact.id] = contact
        self.all_units_by_natural_key[contact.natural_key] = contact
    
    def register_document(self, document: Document) -> None:
        self.documents[document.id] = document
        self.all_units_by_id[document.id] = document
        self.all_units_by_natural_key[document.natural_key] = document
    
    def register_email(self, email: Email) -> None:
        self.emails[email.id] = email
        self.all_units_by_id[email.id] = email
        self.all_units_by_natural_key[email.natural_key] = email
    
    def register_url(self, url: Url) -> None:
        self.urls[url.id] = url
        self.all_units_by_id[url.id] = url
        self.all_units_by_natural_key[url.natural_key] = url




class BusinessInformationDatabase:
    def __init__(self):
        self.business_information: Mapping[str, BusinessInformation] = {}

    def register_business_information(self, business_information: BusinessInformation) -> None:
        self.business_information[business_information.version] = business_information