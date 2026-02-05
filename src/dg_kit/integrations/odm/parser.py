from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from typing import Mapping, Optional, Set, Tuple

from dg_kit.base.logical_model import LogicalModelsDatabase
from dg_kit.base.business_information import BusinessInformationDatabase

from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.dataclasses.logical_model import (
    EntityIdentifier,
    Entity,
    Attribute,
    Relation
)

from dg_kit.base.business_information import BusinessInformation
from dg_kit.base.dataclasses.business_information import (
    Contact,
    Team,
    Email,
    Url,
    Document
)

from dg_kit.integrations.odm.attr_types import ODMAttributeTypesMapping


class ODMParser:
    def __init__(self, odm_project_path: Path):
        if not isinstance(odm_project_path, Path):
            odm_project_path = Path(odm_project_path)
        if not odm_project_path.is_file() and not odm_project_path.name.endswith(".dmd"):
            raise ValueError(f"odm_project_path must be a valid Oracle Data Modeler project (.dmd) file, got: {odm_project_path}")

        self.odm_project_path = odm_project_path

        self.model_name = self.odm_project_path.stem
        self.model_assets_path = self.odm_project_path.parent / self.model_name

        if not self.model_assets_path.is_dir():
            raise FileNotFoundError(
                f"Expected project folder named '{self.model_name}' next to {self.model_name}.dmd, "
                f"but assets folder {self.model_assets_path} not found. "
                "ODM project is corrupted!"
            )

        self.logical_model_path = self.model_assets_path / "logical"
        self.entites_path = self.logical_model_path / "entity"
        self.relations_path = self.logical_model_path / "relation"

        self.business_information_path = self.model_assets_path / "businessinfo"
        self.contacts_path = self.business_information_path / "contact"
        self.documents_path = self.business_information_path / "document"
        self.emails_path = self.business_information_path / "email"
        self.urls_path = self.business_information_path / "url"
        self.parties_path = self.business_information_path / "party"

        self.LM = LogicalModel(self.model_name)
        self.BI = BusinessInformation(self.model_name)

        self.LM.all_lm_units_by_odm_id = {}
        self.BI.all_bi_units_by_odm_id = {}

    def _parse_responsible_parties(self, elem: ET.Element) -> Optional[Set[str]]:
        parties =tuple([self.BI.all_bi_units_by_odm_id[p.text] for p in elem.findall("./responsibleParties/party")])
        return parties or tuple()


    def _parse_documents(self, elem: ET.Element) -> Optional[Set[str]]:
        docs_elem = elem.find("./documents")

        if docs_elem is None:
            return tuple()

        documents_ids = docs_elem.attrib.get("usedDucuments").split(' ')
        documents = tuple([self.BI.all_bi_units_by_odm_id[document_id] for document_id in documents_ids])

        return documents


    def _parse_dt_utc(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        # Example: "2025-12-15 12:01:55 UTC"
        s = s.strip()
        if s.endswith(" UTC"):
            s = s[:-4]
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


    def _parse_bool(self, text: Optional[str]) -> Optional[bool]:
        if text is None:
            return None
        t = text.strip().lower()
        if t == "true":
            return True
        if t == "false":
            return False
        return None


    def _parse_dynamic_properties(self, elem: ET.Element) -> dict[str, str]:
        """
        Parse Oracle Data Modeler <propertyMap><property name="..." value="..."/></propertyMap>
        and return a flat dict {name: value}.

        Works for both Entity and Attribute XML elements.
        - Ignores empty/missing names
        - Keeps empty values as "" (so you can distinguish "present but blank")
        - If duplicate names exist, the last one wins (matches typical override behavior)
        """
        props: dict[str, str] = {}

        prop_map = elem.find("./propertyMap")
        if prop_map is None:
            return props

        for p in prop_map.findall("./property"):
            name = (p.attrib.get("name") or "").strip()
            if not name:
                continue
            value = (p.attrib.get("value") or "")
            props[name] = value

        return props


    def _parse_entity_identifiers(self, entity_id, elem: ET.Element) -> Tuple[EntityIdentifier]:
        identifiers: Set[EntityIdentifier] = set()

        for ident in elem.findall("./identifiers/identifier"):
            ident_id = ident.attrib.get("id")
            if not ident_id:
                continue

            name = ident.attrib.get("name")

            pk_txt = ident.findtext("./pk")
            is_pk = pk_txt == "true"

            used_attributes_ids = tuple(
                [a.text for a in ident.findall("./usedAttributes/attributeRef")]
            )

            entity_identifier = EntityIdentifier(
                natural_key=ident_id,
                name=name,
                is_pk=is_pk,
                entity_id=entity_id,
                used_attributes_ids=used_attributes_ids
            )

            
            identifiers.add(entity_identifier)

        return tuple(identifiers)
    

    def parse_bi(self) -> BusinessInformation:
        # Documents
        for seg in self.documents_path.iterdir():
            for document_xml in seg.iterdir():
                xml_root = ET.parse(document_xml).getroot()

                document_dynamic_props = self._parse_dynamic_properties(xml_root)

                document = Document(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    reference=document_dynamic_props.get('reference')
                )

                self.BI.register_document(document)
                self.BI.all_bi_units_by_odm_id[xml_root.attrib['id']] = document


        # Emails
        for seg in self.emails_path.iterdir():
            for email_xml in seg.iterdir():
                xml_root = ET.parse(email_xml).getroot()

                email = Email(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    email_address=xml_root.findtext('emailAddress'),
                )

                self.BI.register_email(email)
                self.BI.all_bi_units_by_odm_id[xml_root.attrib['id']] = email


        # URLs
        for seg in self.urls_path.iterdir():
            for url_xml in seg.iterdir():
                xml_root = ET.parse(url_xml).getroot()

                url = Url(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    url=xml_root.findtext('url'),
                )

                self.BI.register_url(url)
                self.BI.all_bi_units_by_odm_id[xml_root.attrib['id']] = url


        # Contacts
        for seg in self.contacts_path.iterdir():
            for contact_xml in seg.iterdir():
                xml_root = ET.parse(contact_xml).getroot()
                
                emails = tuple([self.BI.all_bi_units_by_odm_id[p.text] for p in xml_root.findall("./emails/email")])
                urls = tuple([self.BI.all_bi_units_by_odm_id[p.text] for p in xml_root.findall("./urls/urls")])

                contact = Contact(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    emails=emails if emails else tuple(),
                    urls=urls if urls else tuple()
                )

                self.BI.register_contact(contact)
                self.BI.all_bi_units_by_odm_id[xml_root.attrib['id']] = contact


        # Parties
        for seg in self.parties_path.iterdir():
            for party_xml in seg.iterdir():
                xml_root = ET.parse(party_xml).getroot()
                
                contacts = tuple([self.BI.all_bi_units_by_odm_id[p.text] for p in xml_root.findall("./contacts/contact")])

                team = Team(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    contacts=contacts
                )

                self.BI.register_team(team)
                self.BI.all_bi_units_by_odm_id[xml_root.attrib['id']] = team

        return self.BI


    def parse_lm(self) -> LogicalModel:
        dependencies = {}
        for seg in self.entites_path.iterdir():
            for entity_xml in seg.iterdir():
                xml_root = ET.parse(entity_xml).getroot()

                entity_id = xml_root.attrib['id']

                entity_dynamic_props = self._parse_dynamic_properties(xml_root)
                entity_identifiers = self._parse_entity_identifiers(xml_root.attrib['id'], xml_root)

                entity_responsible_parties = tuple(self._parse_responsible_parties(xml_root))

                entity_domain = entity_dynamic_props.get("domain")

                entity_linked_attribute_ids = []
                entity_attributes_xml = xml_root.findall('./attributes/Attribute')
                for attr_xml in entity_attributes_xml:

                    attribute_dynamic_props = self._parse_dynamic_properties(attr_xml)
                    attribute_responsible_parties = tuple(self._parse_responsible_parties(attr_xml)) or entity_responsible_parties

                    referenced_attribute_id = attr_xml.findtext('./referedAttribute')
                    if referenced_attribute_id:
                        if entity_id in dependencies:
                            dependencies[entity_id].append(referenced_attribute_id)
                        else:
                            dependencies[entity_id] = [referenced_attribute_id]
                        continue
                    
                    attr_pm_map_str = attribute_dynamic_props.get("pm_map")
                    attr_pm_map_tuple = tuple(attr_pm_map_str.split(',')) if attr_pm_map_str else ()

                    attr_master_source_systems_str = attribute_dynamic_props.get("master_source_systems")
                    attr_master_source_systems_tuple = tuple(attr_master_source_systems_str.split(',')) if attr_master_source_systems_str else ()

                    attribute = Attribute(
                        natural_key=attr_xml.attrib["name"],
                        entity_id=entity_id,
                        name=attr_xml.attrib.get("name", ""),
                        data_type=ODMAttributeTypesMapping.get(attr_xml.findtext("./logicalDatatype"), 'type missing in mapping'),
                        sensitivity_type=(attr_xml.findtext("./sensitiveType") or "Not sensitive"),
                        description=(attr_xml.findtext("./comment") or ""),
                        documents=self._parse_documents(attr_xml),
                        pm_map=attr_pm_map_tuple,
                        domain=attribute_dynamic_props.get("domain", entity_domain),
                        master_source_systems=attr_master_source_systems_tuple,
                        responsible_parties=attribute_responsible_parties,
                        created_by=(attr_xml.findtext("./createdBy") or "").strip() or None,
                        created_time=self._parse_dt_utc((attr_xml.findtext("./createdTime") or "").strip()),
                    )

                    self.LM.register_attribute(attribute)
                    entity_linked_attribute_ids.append(attribute.id)
                    self.LM.all_lm_units_by_odm_id[attr_xml.attrib['id']] = attribute

                entity_pm_map_str = entity_dynamic_props.get("pm_map")
                entity_pm_map_tuple = entity_pm_map_str.split(',') if entity_pm_map_str else tuple()

                entity_master_source_systems_str = entity_dynamic_props.get("master_source_systems")
                entity_master_source_systems_tuple = entity_master_source_systems_str.split(',') if entity_master_source_systems_str else tuple()
                
                entity = Entity(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    description=xml_root.findtext('comment') if xml_root.findtext('comment') is not None else "",
                    identifiers=entity_identifiers,
                    attributes=tuple(entity_linked_attribute_ids),
                    responsible_parties=entity_responsible_parties,
                    documents=self._parse_documents(xml_root),
                    pm_map=entity_pm_map_tuple,
                    domain=entity_domain,
                    master_source_systems=entity_master_source_systems_tuple,
                    created_by=None,
                    created_time=None,
                )

                self.LM.register_entity(entity)
                self.LM.all_lm_units_by_odm_id[entity_id] = entity

        for seg in self.relations_path.iterdir():
            for relation_xml in seg.iterdir():
                xml_root = ET.parse(relation_xml).getroot()

                relation_dynamic_props = self._parse_dynamic_properties(xml_root)

                relation_responsible_parties = tuple(self._parse_responsible_parties(xml_root))

                relation_pm_map_str = relation_dynamic_props.get("pm_map")
                relation_pm_map_tuple = relation_pm_map_str.split(',') if relation_pm_map_str else tuple()

                relation_dynamic_props_str = relation_dynamic_props.get("master_source_systems")
                relation_dynamic_props_tuple = relation_dynamic_props_str.split(',') if relation_dynamic_props_str else tuple()

                relation = Relation(
                    natural_key=xml_root.attrib['name'],
                    name=xml_root.attrib['name'],
                    domain=relation_dynamic_props.get("domain"),
                    description=xml_root.findtext('comment') if xml_root.findtext('comment') is not None else "",
                    pm_map=relation_pm_map_tuple,
                    master_source_systems=relation_dynamic_props_tuple,
                    responsible_parties=relation_responsible_parties,
                    documents=self._parse_documents(xml_root),
                    source_entity_id=self.LM.all_lm_units_by_odm_id[xml_root.findtext('sourceEntity')].id,
                    target_entity_id=self.LM.all_lm_units_by_odm_id[xml_root.findtext('targetEntity')].id,
                    optional_source=xml_root.findtext('optionalSource'),
                    optional_target=xml_root.findtext('optionalTarget'),
                    source_cardinality=xml_root.findtext('sourceCardinality'),
                    target_cardinality=xml_root.findtext('targetCardinalityString'),
                    created_by=None,
                    created_time=None,
                )

                self.LM.register_relation(relation)
                self.LM.all_lm_units_by_odm_id[xml_root.attrib['id']] = relation

        
        for dependent_entity_odm_id, list_of_referenced_attributes in dependencies.items():
            for attribute_odm_id in list_of_referenced_attributes:
                self.LM.register_dependency(self.LM.all_lm_units_by_odm_id[dependent_entity_odm_id], self.LM.all_units_by_id[self.LM.all_lm_units_by_odm_id[attribute_odm_id].id])

        return self.LM


class ODMVersionedProjectParser:
    def __init__(self, odm_project_path: Path):
        if not isinstance(odm_project_path, Path):
            odm_project_path = Path(odm_project_path)
        if not odm_project_path.is_dir():
            raise ValueError(f"odm_historical_projects_path must be a valid directory, got: {odm_project_path}")

        self.odm_project_path = odm_project_path

        self.odm_projects_paths = []
        dmd_files = list(self.odm_project_path.glob("*.dmd"))
        if dmd_files:
            for dmd_file in dmd_files:
                self.odm_projects_paths.append(dmd_file)

        self.LMDatabse = LogicalModelsDatabase()
        self.BIDatabase = BusinessInformationDatabase()

        self.parse_project()                
    

    def parse_project(self) -> Mapping[str, LogicalModel]:
        for model_path in self.odm_projects_paths:
            parser = ODMParser(model_path)
            bi = parser.parse_bi()
            self.BIDatabase.register_business_information(bi)
            lm = parser.parse_lm()
            self.LMDatabse.register_logical_model(lm)
        
        return None


    def get_model(self, model_name: str) -> LogicalModel:
        if model_name not in self.LMDatabse.logical_models:
            raise KeyError(f"Logical Model '{model_name}' not found in ODM database")

        return self.LMDatabse.logical_models[model_name]
    

    def get_bi(self, bi_name: str) -> BusinessInformation:
        if bi_name not in self.BIDatabase.business_information:
            raise KeyError(f"BusinessInformation '{bi_name}' not found in ODM database")
        
        return self.BIDatabase.business_information[bi_name]