"""Tests for shared enumerations, including Python 3.10 compatibility."""

from __future__ import annotations

import importlib
import logging

from dg_kit.base.enums import ConventionRuleSeverity, DataUnitType


def test_members_behave_like_their_string_values() -> None:
    assert ConventionRuleSeverity.ERROR == "error"
    assert str(ConventionRuleSeverity.ERROR) == "error"
    assert f"{DataUnitType.ENTITY}" == "entity"
    assert ConventionRuleSeverity("warning") is ConventionRuleSeverity.WARNING


def test_severity_selects_logger_method() -> None:
    # dg_kit test logs each breach with getattr(logger, severity)
    logger = logging.getLogger(__name__)

    assert getattr(logger, ConventionRuleSeverity.ERROR) == logger.error


def test_test_command_imports() -> None:
    importlib.import_module("dg_kit.commands.test")
