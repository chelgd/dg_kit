from __future__ import annotations

from typing import List

from dg_kit.base.physical_model import PhysicalModel
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.dataclasses.convention import (
    ConventionRule,
    ConventionRuleFn,
    ConventionBreach,
)


class Convention:
    def __init__(self, name: str):
        self.name = name
        self.rules: List[ConventionRule] = []

    def rule(
        self,
        name: str,
        severity: ConventionRuleSeverity,
        description: str,
    ):
        def rule_registry(fn: ConventionRuleFn) -> ConventionRuleFn:
            self.rules.append(ConventionRule(name, severity, description, fn))
            return fn

        return rule_registry


class ConventionValidator:
    def __init__(self, lm: LogicalModel, pm: PhysicalModel, convention: Convention):
        self.lm = lm
        self.pm = pm
        self.convention = convention

    def validate(self) -> List[ConventionBreach]:
        issues: List[ConventionBreach] = []

        for rule in self.convention.rules:
            res = rule.fn(self.lm, self.pm)
            for issue in res:
                issue = ConventionBreach(
                    severity=rule.severity,
                    message=issue.message,
                    unit_id=issue.unit_id,
                    unit_nk=issue.unit_nk,
                )
                issues.append(issue)

        return issues
