"""Convention rule registration and validation orchestration."""

from __future__ import annotations

from typing import List, Any
import logging
import re

from dg_kit.base.physical_model import PhysicalModel
from dg_kit.base.logical_model import LogicalModel
from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.dataclasses.convention import (
    ConventionRule,
    ConventionRuleFn,
    ConventionBreach,
)


logger = logging.getLogger(__name__)


class Convention:
    """Store convention rules and execute convention checks."""

    def __init__(self, name: str, convention_config: dict[str, Any] = None):
        """Initialize a convention definition from configuration.

        :param name: Convention name.
        :type name: str
        :param convention_config: Convention settings and rule definitions.
        :type convention_config: dict[str, Any] | None
        """
        self.name = name
        self.convention_config = convention_config
        self.rules: List[ConventionRule] = []

        if self.convention_config:
            for rule_name in convention_config["rules"]:
                self.rules.append(
                    ConventionRule(
                        name=rule_name,
                        severity=ConventionRuleSeverity(
                            convention_config["rules"][rule_name]["severity"]
                        ),
                        description=convention_config["rules"][rule_name][
                            "description"
                        ],
                        fn=getattr(self, rule_name),
                    )
                )

    def rule(
        self,
        name: str,
        severity: ConventionRuleSeverity,
        description: str,
    ):
        """Register a validation rule on the convention instance.

        :param name: Rule name.
        :type name: str
        :param severity: Default severity assigned to rule breaches.
        :type severity: ConventionRuleSeverity
        :param description: Human-readable rule description.
        :type description: str
        :returns: Decorator that registers the wrapped rule function.
        :rtype: ConventionRuleFn
        """
        def rule_registry(fn: ConventionRuleFn) -> ConventionRuleFn:
            self.rules.append(ConventionRule(name, severity, description, fn))
            return fn

        return rule_registry

    def allowed_dependencies(self, LM: LogicalModel, PM: PhysicalModel, **kwargs):
        """Validate that dependencies only target allowed layers.

        :param LM: Logical model, unused but accepted for rule signature compatibility.
        :type LM: LogicalModel
        :param PM: Physical model containing dependency information.
        :type PM: PhysicalModel
        :param kwargs: Rule configuration with allowed layer mappings and severity.
        :type kwargs: dict[str, Any]
        :returns: Detected convention breaches.
        :rtype: list[ConventionBreach]
        """
        issues = []
        missing_allowed_dependencies = []
        rules_by_layer = kwargs.get("rules", {})
        for dependent_id, dependencies_set in PM.dependencies.items():
            for dependency_id in dependencies_set:
                dependent = PM.all_units_by_id[dependent_id]
                dependent_layer = PM.layers[dependent.layer_id]

                dependency = PM.all_units_by_id[dependency_id]
                dependency_layer = PM.layers[dependency.layer_id]

                allowed_dependency_layers = rules_by_layer.get(dependent_layer.name)
                if allowed_dependency_layers is None:
                    if dependent_layer.name not in missing_allowed_dependencies:
                        message = (
                            f"Missing allowed_dependencies rule for dependent layer "
                            f"'{dependent_layer.name}'"
                        )
                        issues.append(
                            ConventionBreach(
                                severity=ConventionRuleSeverity.WARNING,
                                message=message,
                            )
                        )
                        missing_allowed_dependencies.append(dependent_layer.name)
                        continue
                    else:
                        continue

                if dependency_layer.name not in allowed_dependency_layers:
                    issue = ConventionBreach(
                        severity=ConventionRuleSeverity(kwargs["severity"]),
                        message=f"{dependent.name} from {dependent_layer.name} layer depends on {dependency.name} which is from {dependency_layer.name} layer",
                    )
                    issues.append(issue)

        return issues

    def regex_by_layer(self, LM: LogicalModel, PM: PhysicalModel, **kwargs):
        """Validate table names against layer-specific regular expressions.

        :param LM: Logical model, unused but accepted for rule signature compatibility.
        :type LM: LogicalModel
        :param PM: Physical model containing table definitions.
        :type PM: PhysicalModel
        :param kwargs: Rule configuration with regex definitions and severity.
        :type kwargs: dict[str, Any]
        :returns: Detected convention breaches.
        :rtype: list[ConventionBreach]
        """
        issues = []

        regexp_by_layer_name = {}

        for regexp_name in kwargs["rules"]:
            if kwargs["rules"][regexp_name]["layer"] in regexp_by_layer_name:
                regexp_by_layer_name[kwargs["rules"][regexp_name]["layer"]].append(
                    re.compile(
                        kwargs["rules"][regexp_name]["regex"]["string"], re.IGNORECASE
                    )
                )
            else:
                regexp_by_layer_name[kwargs["rules"][regexp_name]["layer"]] = [
                    re.compile(
                        kwargs["rules"][regexp_name]["regex"]["string"], re.IGNORECASE
                    )
                ]

        for table in PM.tables.values():
            if PM.layers[table.layer_id].name in regexp_by_layer_name:
                regexp_gates = {
                    comp_regexp.match(table.name)
                    for comp_regexp in regexp_by_layer_name[
                        PM.layers[table.layer_id].name
                    ]
                }
                if not any(regexp_gates):
                    issues.append(
                        ConventionBreach(
                            severity=ConventionRuleSeverity(kwargs["severity"]),
                            message=f"Table '{table.name}' violates naming convention.",
                        )
                    )

        return issues


class ConventionValidator:
    """Run all configured convention rules against logical and physical models."""

    def __init__(self, lm: LogicalModel, pm: PhysicalModel, convention: Convention):
        """Initialize the validator.

        :param lm: Logical model to validate.
        :type lm: LogicalModel
        :param pm: Physical model to validate.
        :type pm: PhysicalModel
        :param convention: Convention containing validation rules.
        :type convention: Convention
        """
        self.lm = lm
        self.pm = pm
        self.convention = convention

    def validate(self) -> List[ConventionBreach]:
        """Execute all configured rules and collect breaches.

        :returns: Validation issues found across all rules.
        :rtype: list[ConventionBreach]
        """
        issues: List[ConventionBreach] = []

        logger.info(
            f"Starting model validation according to convention: {self.convention.name}..."
        )
        for rule in self.convention.rules:
            res = rule.fn(
                self.lm,
                self.pm,
                **self.convention.convention_config["rules"][rule.name],
            )
            for issue in res:
                issues.append(issue)

        return issues
