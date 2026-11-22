"""Tests for the dbt physical model parser and its config wiring."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from dg_kit.base.physical_model import PhysicalModel
from dg_kit.commands.common import parse_physical_model
from dg_kit.integrations.dbt.parser import DBTParser


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(path: Path, data: dict) -> None:
    _write(path, yaml.safe_dump(data, sort_keys=False))


def _column(name: str, data_type: str | None = "String") -> dict:
    column = {"name": name, "description": f"{name} column"}
    if data_type is not None:
        column["data_type"] = data_type
    return column


def _model(path: Path, name: str, sql: str, columns: list[dict]) -> None:
    _write_yaml(path / f"{name}.yml", {"models": [{"name": name, "columns": columns}]})
    _write(path / f"{name}.sql", sql)


def _table_nks(pm: PhysicalModel) -> set[str]:
    return {table.nk for table in pm.tables.values()}


def _dependency_nks(pm: PhysicalModel) -> set[tuple[str, str]]:
    return {
        (pm.tables[dependent_id].nk, pm.tables[dependency_id].nk)
        for dependent_id, dependency_ids in pm.dependencies.items()
        for dependency_id in dependency_ids
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repository with a dbt project and a ``sources/`` folder outside it."""
    dbt = tmp_path / "transform" / "dbt"
    _write_yaml(
        dbt / "dbt_project.yml",
        {
            "name": "sample",
            "models": {
                # non-mapping "+" configs next to the project must be skipped
                "+on_schema_change": "append_new_columns",
                "+full_refresh": False,
                "sample": {"raw": {}, "core": {}, "interim": {}},
            },
        },
    )
    models = dbt / "models"
    _model(
        models / "raw",
        "users",
        "select * from {{ source('app_export', 'users') }}",
        [_column("user_id")],
    )
    _model(
        models / "core",
        "dim_users_act",
        "select * from {{ ref('users') }}",
        [_column("user_id")],
    )
    _model(
        models / "core",
        "dim_scratch_act",
        "select 1",
        [_column("x")],
    )
    # legacy model: column "a" has no data_type, column "b" has neither field
    _model(
        models / "interim",
        "legacy",
        "select * from {{ ref('dim_users_act') }}",
        [_column("a", data_type=None), {"name": "b"}],
    )
    _write_yaml(
        tmp_path / "sources" / "app.yml",
        {
            "version": 2,
            "sources": [
                {
                    "name": "app_export",
                    "tables": [{"name": "users", "columns": [_column("id")]}],
                }
            ],
        },
    )
    return tmp_path


def _parser(repo: Path, **kwargs) -> DBTParser:
    return DBTParser(repo / "transform" / "dbt", "v1", **kwargs)


def test_sources_outside_models_are_not_seen_by_default(repo: Path) -> None:
    pm = _parser(repo).parse_pm()

    assert "app_export.users" not in _table_nks(pm)


def test_source_paths_directory_adds_sources_and_dependencies(repo: Path) -> None:
    pm = _parser(repo, source_paths=[repo / "sources"]).parse_pm()

    assert "app_export.users" in _table_nks(pm)
    assert ("raw.users", "app_export.users") in _dependency_nks(pm)


def test_source_paths_accepts_a_file(repo: Path) -> None:
    pm = _parser(repo, source_paths=[repo / "sources" / "app.yml"]).parse_pm()

    assert "app_export.users" in _table_nks(pm)


def test_missing_source_path_raises(repo: Path) -> None:
    with pytest.raises(FileNotFoundError, match="dbt source path not found"):
        _parser(repo, source_paths=[repo / "missing"])


def test_ignore_directory_skips_its_yml_and_sql(repo: Path) -> None:
    pm = _parser(repo, ignore=["models/interim/"]).parse_pm()

    assert "interim.legacy" not in _table_nks(pm)
    assert "core.dim_users_act" in _table_nks(pm)


def test_ignore_supports_gitignore_negation(repo: Path) -> None:
    ignore = ["models/core/*", "!models/core/dim_users_act.*"]

    pm = _parser(repo, ignore=ignore).parse_pm()

    assert "core.dim_users_act" in _table_nks(pm)
    assert "core.dim_scratch_act" not in _table_nks(pm)


def test_ignoring_only_the_yml_of_a_model_names_the_sql(repo: Path) -> None:
    parser = _parser(repo, ignore=["models/interim/legacy.yml"])

    with pytest.raises(Exception, match="ignore its .yml and .sql together"):
        parser.parse_pm()


def test_columns_without_data_type_or_description_are_kept(
    repo: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="dg_kit.integrations.dbt.parser"):
        pm = _parser(repo).parse_pm()

    columns = {column.nk: column for column in pm.columns.values()}
    assert columns["interim.legacy.a"].data_type == ""
    assert columns["interim.legacy.b"].data_type == ""
    assert columns["interim.legacy.b"].description == ""
    assert "interim.legacy has columns without data_type: a, b" in caplog.text


@pytest.mark.parametrize(
    "kwargs",
    [{"ignore": "models/interim/"}, {"source_paths": "sources"}],
)
def test_single_value_instead_of_list_is_rejected(repo: Path, kwargs: dict) -> None:
    with pytest.raises(TypeError, match="must be a list"):
        _parser(repo, **kwargs)


def test_parse_physical_model_reads_config_relative_to_cwd(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(repo)
    config = {
        "version": "v1",
        "physical_model": {
            "engine": "dbt",
            "path": "transform/dbt",
            "source_paths": ["sources"],
            "ignore": ["models/interim/"],
        },
    }

    pm = parse_physical_model(config)

    assert "app_export.users" in _table_nks(pm)
    assert "interim.legacy" not in _table_nks(pm)


def test_parse_physical_model_without_optional_keys(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(repo)

    pm = parse_physical_model(
        {"version": "v1", "physical_model": {"path": "transform/dbt"}}
    )

    assert "interim.legacy" in _table_nks(pm)
