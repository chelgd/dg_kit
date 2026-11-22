"""Enumerations shared across conventions and data catalog models."""

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        """Python 3.10 stand-in for :class:`enum.StrEnum` (added in 3.11).

        Members compare equal to, and format as, their string values.
        """

        __str__ = str.__str__
        __format__ = str.__format__


class ConventionRuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DataUnitType(StrEnum):
    ENTITY = "entity"
    ATTRIBUTE = "attribute"
    RELATION = "relation"


class DataCatalogRowProperties(StrEnum):
    ID = "Data unit id"
    UNIT_TYPE = "Data unit type"
    TITLE = "Data unit"
    DOMAIN = "Domain"
