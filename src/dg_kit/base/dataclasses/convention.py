from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Set

from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.physical_model import PhysicalModel

@dataclass(frozen=True, slots=True)
class ConventionBreach:
    severity: ConventionRuleSeverity
    message: str
    unit_id: Optional[str] = None
    unit_natural_key: Optional[str] = None


class ConventionRuleFn(Protocol):
    def __call__(
        self,
        lm: LogicalModel,
        pm: PhysicalModel
    ) -> Set[ConventionBreach]:
        ...


@dataclass(frozen=True, slots=True)
class ConventionRule:
    name: str
    severity: ConventionRuleSeverity
    description: str
    fn: ConventionRuleFn