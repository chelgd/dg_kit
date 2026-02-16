from enum import StrEnum


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
