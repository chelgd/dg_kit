"""Implementation of the ``dg_kit test`` command.

This module loads logical and physical models, applies configured
convention rules, and reports validation breaches.
"""

from __future__ import annotations

import logging
from typing import Any, List


from pathlib import Path
from dg_kit.base.enums import ConventionRuleSeverity
from dg_kit.base.dataclasses.convention import ConventionBreach
from dg_kit.base.convention import Convention, ConventionValidator
from dg_kit.integrations.dbt.parser import DBTParser
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser


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

    logger.info("Starting model validation according to convention...")

    issues: List[ConventionBreach] = []

    odm_project_path = Path(config.get("logical_model", {}).get("path"))
    dbt_project_path = Path(config.get("physical_model", {}).get("path"))

    dbt_parser = DBTParser(dbt_project_path, config["version"])
    PM = dbt_parser.parse_pm()

    odm_project = ODMVersionedProjectParser(odm_project_path=odm_project_path)
    odm_project.parse_version(config["version"], PM)
    LM = odm_project.get_model(config["version"])

    convention = Convention(config["name"], convention_config)

    convention_validator = ConventionValidator(LM, PM, convention)
    issues += convention_validator.validate()
    issues += odm_project.parsing_issues[config["version"]]

    sys_exit_status = 0

    for issue in issues:
        getattr(logger, issue.severity)(issue.message)
        if issue.severity == ConventionRuleSeverity.ERROR:
            sys_exit_status = 1

    if sys_exit_status == 0:
        logger.info("Validation successful")

    return sys_exit_status
