"""Core abstractions and orchestration for data catalog synchronization.

This module defines the catalog engine protocol and the in-memory catalog
manager used by pull and sync commands.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Tuple
from os import environ
import logging
import pickle
from pathlib import Path

from dg_kit.base.enums import DataUnitType
from dg_kit.base.dataclasses.data_catalog import (
    DataCatalogRow,
    EntityPage,
    AttributePage,
    RelationPage,
    ObjectReference,
    IndexedCatalog,
)
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.dataclasses.logical_model import (
    Entity,
    Attribute,
    Relation,
)

logger = logging.getLogger(__name__)


class DataCatalogEngine(ABC):
    """Define the storage interface for a data catalog backend."""

    @abstractmethod
    def pull_data_catalog(
        self,
    ) -> Tuple[
        Dict[str, DataCatalogRow], Dict[str, EntityPage | AttributePage | RelationPage]
    ]:
        """Fetch the full catalog state from the backing store.

        :returns: Indexed catalog content keyed by object identifier.
        :rtype: tuple[dict[str, DataCatalogRow], dict[str, EntityPage | AttributePage | RelationPage]]
        """
        raise NotImplementedError

    @abstractmethod
    def update_row(self, data_catalog_row: DataCatalogRow) -> None:
        """Persist an updated catalog row.

        :param data_catalog_row: Row metadata to update.
        :type data_catalog_row: DataCatalogRow
        """
        raise NotImplementedError

    @abstractmethod
    def update_page(
        self, data_unit_page: EntityPage | AttributePage | RelationPage
    ) -> None:
        """Persist an updated data unit page.

        :param data_unit_page: Page payload to update.
        :type data_unit_page: EntityPage | AttributePage | RelationPage
        """
        raise NotImplementedError

    @abstractmethod
    def add_page(
        self, data_unit_page: EntityPage | AttributePage | RelationPage
    ) -> None:
        """Create a new data unit page in the backing store.

        :param data_unit_page: Page payload to create.
        :type data_unit_page: EntityPage | AttributePage | RelationPage
        """
        raise NotImplementedError

    @abstractmethod
    def add_row(self, data_catalog_row: DataCatalogRow) -> ObjectReference:
        """Create a new catalog row.

        :param data_catalog_row: Row metadata to create.
        :type data_catalog_row: DataCatalogRow
        :returns: Reference to the created remote object.
        :rtype: ObjectReference
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id: str) -> None:
        """Delete a catalog object by identifier.

        :param id: Catalog object identifier.
        :type id: str
        """
        raise NotImplementedError


class DataCatalog:
    """Manage a locally cached view of the data catalog."""

    def __init__(
        self,
        engine: DataCatalogEngine,
        config: Dict,
    ):
        """Initialize the catalog and load the cached or remote state.

        :param engine: Backend engine used for persistence operations.
        :type engine: DataCatalogEngine
        :param config: Project configuration containing catalog settings.
        :type config: dict
        """
        self.engine = engine
        self.config = config
        self.artifact_path = Path(
            f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl"
        )

        if self.artifact_path.exists():
            try:
                logger.info(f"Initiating indexed DB from {self.artifact_path}.")
                self.indexed_catalog: IndexedCatalog = self.load_from_local()
            except Exception:
                logger.error(
                    f"Couldn't initiate indexed catalog localy from {self.artifact_path}. Pulling catalog from remote."
                )
                self.pull_data_catalog()
        else:
            logger.info(
                f"Couldn't find indexed catalog localy at {self.artifact_path}. Pulling catalog from remote."
            )
            self.pull_data_catalog()

    def pull_data_catalog(self):
        """Refresh the local cache from the remote catalog backend."""
        self.indexed_catalog = self.engine.pull_data_catalog()
        self.save_to_local()

    def get_row_by_id(self, id: str) -> DataCatalogRow:
        """Return a catalog row by identifier.

        :param id: Catalog object identifier.
        :type id: str
        :returns: Matching row if present.
        :rtype: DataCatalogRow
        """
        return self.indexed_catalog.row_by_id.get(id)

    def get_page_by_id(self, id: str) -> Entity | Attribute | Relation:
        """Return a catalog page by identifier.

        :param id: Catalog object identifier.
        :type id: str
        :returns: Matching page if present.
        :rtype: Entity | Attribute | Relation
        """
        return self.indexed_catalog.page_by_id.get(id)

    def update_row(self, data_catalog_row: DataCatalogRow) -> None:
        """Update a row in memory, remotely, and in the local checkpoint.

        :param data_catalog_row: Row metadata to persist.
        :type data_catalog_row: DataCatalogRow
        """
        self.indexed_catalog.row_by_id[data_catalog_row.id] = data_catalog_row
        self.engine.update_row(data_catalog_row)
        self.save_to_local()

    def update_page(self, page: EntityPage | AttributePage | RelationPage) -> None:
        """Update a page in memory, remotely, and in the local checkpoint.

        :param page: Page payload to persist.
        :type page: EntityPage | AttributePage | RelationPage
        """
        self.indexed_catalog.page_by_id[page.id] = page
        self.engine.update_page(page)
        self.save_to_local()

    def add_page(self, page: EntityPage | AttributePage | RelationPage) -> None:
        """Add a new page to the catalog.

        :param page: Page payload to create.
        :type page: EntityPage | AttributePage | RelationPage
        :raises KeyError: If a page with the same identifier already exists.
        """
        if page.id in self.indexed_catalog.page_by_id:
            raise KeyError(
                f"Data unit page with id='{page.id}' already exists. Use update instead."
            )

        self.indexed_catalog.page_by_id[page.id] = page
        self.engine.add_page(page)
        self.save_to_local()

    def add_row(self, raw_data_catalog_row: Dict) -> ObjectReference:
        """Add a new row to the catalog from raw row metadata.

        :param raw_data_catalog_row: Raw row payload expected by the backend.
        :type raw_data_catalog_row: dict
        :returns: Reference to the created remote page.
        :rtype: ObjectReference
        :raises KeyError: If a row with the same identifier already exists.
        """
        if raw_data_catalog_row["id"] in self.indexed_catalog.row_by_id:
            raise KeyError(
                f"Data unit with id='{raw_data_catalog_row['id']}' already exists. Use update instead."
            )

        page_reference = self.engine.add_row(raw_data_catalog_row)
        data_catalog_row = DataCatalogRow(
            id=raw_data_catalog_row["id"],
            reference=page_reference,
            data_unit_type=raw_data_catalog_row["data_unit_type"],
            data_unit_name=raw_data_catalog_row["data_unit_name"],
            domain=raw_data_catalog_row["domain"],
        )
        self.indexed_catalog.row_by_id[raw_data_catalog_row["id"]] = data_catalog_row
        self.indexed_catalog.reference_by_id[raw_data_catalog_row["id"]] = (
            page_reference
        )
        self.save_to_local()

        return page_reference

    def delete_by_id(self, id: str) -> None:
        """Delete a row and page from the catalog by identifier.

        :param id: Catalog object identifier.
        :type id: str
        """
        self.indexed_catalog.row_by_id.pop(id, None)
        self.indexed_catalog.page_by_id.pop(id, None)
        self.engine.delete_by_id(id)
        self.save_to_local()

    def sync_with_model(
        self,
        LM: LogicalModel,
    ):
        """Synchronize the catalog contents with the logical model.

        :param LM: Logical model used as the source of truth.
        :type LM: LogicalModel
        """
        lm_ids = set(LM.all_units_by_id)
        row_ids = set(self.indexed_catalog.row_by_id)
        rows_and_lm_intersection = row_ids & lm_ids
        rows_diff = row_ids - lm_ids
        lm_diff = lm_ids - row_ids

        logger.info("Deleting data units from DC...")
        for id in rows_diff:
            self.delete_by_id(id)

        logger.info("Adding new data units...")
        for data_unit_id in lm_diff:
            if data_unit_id in LM.entities:
                data_unit_type = DataUnitType.ENTITY
            elif data_unit_id in LM.attributes:
                data_unit_type = DataUnitType.ATTRIBUTE
            elif data_unit_id in LM.relations:
                data_unit_type = DataUnitType.RELATION

            data_unit = LM.all_units_by_id[data_unit_id]

            raw_data_catalog_row = {
                "id": data_unit.id,
                "data_unit_name": data_unit.name,
                "data_unit_type": data_unit_type,
                "domain": data_unit.domain or "Unknown",
            }

            self.add_row(raw_data_catalog_row)

        for data_unit_id in lm_diff:
            if data_unit_id in LM.entities:
                entity = LM.entities[data_unit_id]

                for identifier in LM.identifiers_by_entity_id[entity.id]:
                    if identifier.is_pk:
                        pk_attributes_references = tuple(
                            [
                                self.indexed_catalog.reference_by_id[
                                    attribute.id
                                ].reference_link
                                for attribute in identifier.attributes
                            ]
                        )
                attributes_references = tuple(
                    [
                        self.indexed_catalog.reference_by_id[
                            attribute.id
                        ].reference_link
                        for attribute in LM.attributes_by_entity_id[entity.id]
                    ]
                )
                relations_references = tuple(
                    [
                        self.indexed_catalog.reference_by_id[relation.id].reference_link
                        for relation in LM.relations_by_entity_id[entity.id]
                    ]
                )

                page = EntityPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[entity.id],
                    data_unit_type=DataUnitType.ENTITY,
                    description=entity.description,
                    pk_attributes_references=pk_attributes_references,
                    attributes_references=attributes_references,
                    relations_references=relations_references,
                    linked_documents=tuple(
                        [document.name for document in entity.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in entity.responsible_parties]
                    ),
                    pm_mapping_references=entity.pm_map,
                    source_systems=entity.source_systems,
                )

            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]

                page = AttributePage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[attribute.id],
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    description=attribute.description,
                    parent_entity_reference=self.indexed_catalog.reference_by_id[
                        attribute.entity_id
                    ].reference_link,
                    data_type=attribute.data_type,
                    sensitivity_type=attribute.sensitivity_type,
                    linked_documents=tuple(
                        [document.name for document in attribute.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in attribute.responsible_parties]
                    ),
                    pm_mapping_references=attribute.pm_map,
                    source_systems=attribute.source_systems,
                )

            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]

                page = RelationPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[relation.id],
                    data_unit_type=DataUnitType.RELATION,
                    description=relation.description,
                    source_entity_reference=self.indexed_catalog.reference_by_id[
                        relation.source_entity_id
                    ].reference_link,
                    target_entity_reference=self.indexed_catalog.reference_by_id[
                        relation.target_entity_id
                    ].reference_link,
                    linked_documents=tuple(
                        [document.name for document in relation.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in relation.responsible_parties]
                    ),
                    pm_mapping_references=relation.pm_map,
                    source_systems=relation.source_systems,
                )

            else:
                logger.error(
                    f"Unexpected data unit id {data_unit_id} while adding pages."
                )
                continue

            self.add_page(page)

        logger.info("Updating updated data units...")
        for data_unit_id in rows_and_lm_intersection:
            if data_unit_id in LM.entities:
                entity = LM.entities[data_unit_id]
                row = DataCatalogRow(
                    id=entity.id,
                    reference=ObjectReference(
                        id=entity.id,
                        reference_link=self.indexed_catalog.reference_by_id[
                            entity.id
                        ].reference_link,
                    ),
                    data_unit_name=entity.name,
                    data_unit_type=DataUnitType.ENTITY,
                    domain=entity.domain
                    or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]
                row = DataCatalogRow(
                    id=attribute.id,
                    reference=ObjectReference(
                        id=attribute.id,
                        reference_link=self.indexed_catalog.reference_by_id[
                            attribute.id
                        ].reference_link,
                    ),
                    data_unit_name=attribute.name,
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    domain=attribute.domain
                    or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]
                row = DataCatalogRow(
                    id=relation.id,
                    reference=ObjectReference(
                        id=relation.id,
                        reference_link=self.indexed_catalog.reference_by_id[
                            relation.id
                        ].reference_link,
                    ),
                    data_unit_name=relation.name,
                    data_unit_type=DataUnitType.RELATION,
                    domain=relation.domain
                    or environ.get("DG_KIT_DEFAULT_DOMAIN", "Unknown"),
                )

            else:
                logger.error(
                    f"Unexpected data unit id {data_unit_id} while updating rows."
                )
                continue

            if row == self.indexed_catalog.row_by_id[data_unit_id]:
                continue
            else:
                self.update_row(row)

        for data_unit_id in rows_and_lm_intersection:
            if data_unit_id in LM.entities:
                entity = LM.entities[data_unit_id]

                for identifier in LM.identifiers_by_entity_id[entity.id]:
                    if identifier.is_pk:
                        pk_attributes_references = tuple(
                            [
                                self.indexed_catalog.reference_by_id[
                                    attribute.id
                                ].reference_link
                                for attribute in identifier.attributes
                            ]
                        )
                attributes_references = tuple(
                    [
                        self.indexed_catalog.reference_by_id[
                            attribute.id
                        ].reference_link
                        for attribute in LM.attributes_by_entity_id[entity.id]
                    ]
                )
                relations_references = tuple(
                    [
                        self.indexed_catalog.reference_by_id[relation.id].reference_link
                        for relation in LM.relations_by_entity_id[entity.id]
                    ]
                )

                page = EntityPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[entity.id],
                    data_unit_type=DataUnitType.ENTITY,
                    description=entity.description,
                    pk_attributes_references=pk_attributes_references,
                    attributes_references=attributes_references,
                    relations_references=relations_references,
                    linked_documents=tuple(
                        [document.name for document in entity.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in entity.responsible_parties]
                    ),
                    pm_mapping_references=entity.pm_map,
                    source_systems=entity.source_systems,
                )

            elif data_unit_id in LM.attributes:
                attribute = LM.attributes[data_unit_id]

                page = AttributePage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[attribute.id],
                    data_unit_type=DataUnitType.ATTRIBUTE,
                    description=attribute.description,
                    parent_entity_reference=self.indexed_catalog.reference_by_id[
                        attribute.entity_id
                    ].reference_link,
                    data_type=attribute.data_type,
                    sensitivity_type=attribute.sensitivity_type,
                    linked_documents=tuple(
                        [document.name for document in attribute.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in attribute.responsible_parties]
                    ),
                    pm_mapping_references=attribute.pm_map,
                    source_systems=attribute.source_systems,
                )

            elif data_unit_id in LM.relations:
                relation = LM.relations[data_unit_id]

                page = RelationPage(
                    id=data_unit_id,
                    reference=self.indexed_catalog.reference_by_id[relation.id],
                    data_unit_type=DataUnitType.RELATION,
                    description=relation.description,
                    source_entity_reference=self.indexed_catalog.reference_by_id[
                        relation.source_entity_id
                    ].reference_link,
                    target_entity_reference=self.indexed_catalog.reference_by_id[
                        relation.target_entity_id
                    ].reference_link,
                    linked_documents=tuple(
                        [document.name for document in relation.documents]
                    ),
                    responsible_parties=tuple(
                        [party.name for party in relation.responsible_parties]
                    ),
                    pm_mapping_references=relation.pm_map,
                    source_systems=relation.source_systems,
                )

            else:
                logger.error(
                    f"Unexpected data unit id {data_unit_id} while updating pages."
                )

                continue

            if page == self.indexed_catalog.page_by_id[data_unit_id]:
                continue
            else:
                self.update_page(page)

    def save_to_local(self) -> None:
        """Serialize the indexed catalog to the local checkpoint file."""
        with open(
            f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl",
            "wb",
        ) as f:
            pickle.dump(self.indexed_catalog, f)

    def load_from_local(self) -> IndexedCatalog:
        """Load the indexed catalog from the local checkpoint file.

        :returns: Deserialized indexed catalog.
        :rtype: IndexedCatalog
        """
        with open(
            f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl",
            "rb",
        ) as f:
            return pickle.load(f)
