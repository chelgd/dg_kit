"""Implementation of the ``dg_kit test`` command.

This module loads logical and physical models, applies configured
convention rules, and reports validation breaches.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List


from pathlib import Path
from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.dataclasses.convention import ConventionBreach
from dg_kit.base.convention import Convention, ConventionValidator
from dg_kit.integrations.dbt.parser import DBTParser
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser

from dg_kit.base.dataclasses.logical_model import Entity, Attribute, Relation

logger = logging.getLogger(__name__)


def run(
    config: dict[str, Any],
    convention_config: dict[str, Any],
) -> int:
    """Validate logical and physical model consistency against a convention.

    :param config: Project configuration with model locations and version info.
    :type config: dict[str, Any]
    :param convention_config: Convention settings and rule definitions.
    :type convention_config: dict[str, Any]
    :returns: Process-style exit status where ``0`` means success.
    :rtype: int
    """
    issues: List[ConventionBreach] = []

    odm_project_path = Path(config.get("logical_model", {}).get("path"))
    dbt_project_path = Path(config.get("physical_model", {}).get("path"))

    dbt_parser = DBTParser(dbt_project_path, config["version"])

    odm_project = ODMVersionedProjectParser(odm_project_path=odm_project_path)

    PM = dbt_parser.parse_pm()
    odm_project.parse_version(config["version"], PM)
    LM = odm_project.get_model(config["version"])

    convention = Convention(config["name"], convention_config)

    convention_validator = ConventionValidator(LM, PM, convention)
    issues += convention_validator.validate()

    lm_objects_by_pm_id: Dict[str, List[Entity | Attribute | Relation]] = {}

    for unit in LM.all_units_by_id.values():
        if not unit.pm_map:
            issues.append(
                ConventionBreach(
                    severity=ConventionRuleSeverity(convention_config['rules']['lm_x_pm_consistency']['severity']),
                    message=f"Missing PM mapping for {unit.name}",
                )
            )
            continue
        else:
            for pm_obj in LM.pm_objects_by_lm_id[unit.id]:
                if pm_obj.id in lm_objects_by_pm_id:
                    lm_objects_by_pm_id[pm_obj.id].append(unit.id)
                else:
                    lm_objects_by_pm_id[pm_obj.id] = [unit.id]

    lm_mapping_layers = []

    for layer in PM.layers.values():
        if layer.name in convention_config["lm_mapping_layers"]:
            lm_mapping_layers.append(layer.id)

    for pm_unit in PM.tables.values():
        if (
            pm_unit.layer_id in lm_mapping_layers
            and pm_unit.id not in lm_objects_by_pm_id
        ):
            layer_name = PM.layers[pm_unit.layer_id].name
            issues.append(
                ConventionBreach(
                    severity=ConventionRuleSeverity(convention_config['rules']['lm_x_pm_consistency']['severity']),
                    message=f"This PM object is not used in LM: {layer_name}.{pm_unit.name}",
                )
            )

    for pm_unit in PM.columns.values():
        if (
            pm_unit.layer_id in lm_mapping_layers
            and pm_unit.id not in lm_objects_by_pm_id
        ):
            layer_name = PM.layers[pm_unit.layer_id].name
            if layer_name in convention_config["technical_fields"]:
                technical_fields = convention_config["technical_fields"][layer_name]
                if pm_unit.name in technical_fields:
                    continue
            table_name = PM.tables[pm_unit.table_id].name
            issues.append(
                ConventionBreach(
                    severity=ConventionRuleSeverity(convention_config['rules']['lm_x_pm_consistency']['severity']),
                    message=f"This PM object is not used in LM: {layer_name}.{table_name}.{pm_unit.name}",
                )
            )

    sys_exit_status = 0

    for issue in issues:
        getattr(logger, issue.severity)(issue.message)
        if issue.severity == ConventionRuleSeverity.ERROR:
            sys_exit_status = 1

    return sys_exit_status
