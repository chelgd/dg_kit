from enum import StrEnum


class ConventionRuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DataUnitType(StrEnum):
    ENTITY = "entity"
    ATTRIBUTE = "attribute"
    RELATION = "relation"
