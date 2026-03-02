from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Set

from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.physical_model import PhysicalModel


@dataclass(frozen=True, slots=True)
class ConventionBreach:
    severity: ConventionRuleSeverity
    message: str


class ConventionRuleFn(Protocol):
    def __call__(
        self, lm: LogicalModel, pm: PhysicalModel, **kwargs: dict
    ) -> Set[ConventionBreach]: ...


@dataclass(frozen=True, slots=True)
class ConventionRule:
    name: str
    severity: ConventionRuleSeverity
    description: str
    fn: ConventionRuleFn
