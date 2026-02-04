from __future__ import annotations

from typing import Optional

from abc import ABC, abstractmethod

from dg_kit.base.dataclasses.data_catalog import DataCatalogRow, EntityTypeDataUnitPageInfo


class DataCatalog(ABC):
    ...