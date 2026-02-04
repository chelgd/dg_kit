from enum import StrEnum, Enum


class ConventionRuleSeverity(StrEnum):
    INFO = "info"
    WARN = "warning"
    ERROR = "error"


class DataUnitType(StrEnum):
    ENTITY = "entity"
    ATTRIBUTE = "attribute"
    RELATION = "relation"