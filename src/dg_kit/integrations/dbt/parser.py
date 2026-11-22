"""Parsers for dbt projects.

This module reads dbt metadata and SQL models to construct physical model
objects and dependency graphs.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

import pathspec
import yaml

from dg_kit.base.dataclasses import id_generator
from dg_kit.base.physical_model import PhysicalModel
from dg_kit.base.dataclasses.physical_model import Table, Column, Layer


_REF_RE = re.compile(
    r"""ref\(\s*(['"])(?P<table_name>[^'"]+)\1\s*(?:,\s*(['"])(?P<schema_name>[^'"]+)\3\s*)?\)""",
    re.IGNORECASE,
)
_SOURCE_RE = re.compile(
    r"""source\(\s*(['"])(?P<schema_name>[^'"]+)\1\s*,\s*(['"])(?P<table_name>[^'"]+)\3\s*\)""",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


class DBTPhysicalModel(PhysicalModel):
    def __init__(self, version: str):
        super().__init__(version)
        self.all_tables_by_nk: dict[str, Table] = {}
        self.all_dbt_tables_by_model: dict[str, Table] = {}


class DBTParser:
    """Build a physical model from a dbt project.

    :param dbt_project_path: dbt project directory containing ``dbt_project.yml``.
    :type dbt_project_path: Path
    :param version: Physical model version label.
    :type version: str
    :param source_paths: Extra files or directories with dbt ``sources`` YAML kept
        outside ``models/``. Directories are searched recursively for ``*.yml``.
    :type source_paths: Iterable[Path | str] | None
    :param ignore: ``.gitignore``-style patterns relative to the dbt project
        directory. Matching YAML and SQL files are not parsed.
    :type ignore: Iterable[str] | None
    """

    def __init__(
        self,
        dbt_project_path: Path,
        version: str,
        source_paths: Iterable[Path | str] | None = None,
        ignore: Iterable[str] | None = None,
    ):
        if not isinstance(dbt_project_path, Path):
            dbt_project_path = Path(dbt_project_path)
        if not dbt_project_path.is_dir():
            raise ValueError(
                f"dbt_project_path must be a valid dbt project directory, got: {dbt_project_path}"
            )

        self.dbt_project_path = dbt_project_path
        self.models_path = self.dbt_project_path / "models"
        self.seeds_path = self.dbt_project_path / "seeds"

        if not self.models_path.is_dir():
            raise FileNotFoundError(
                f"Expected 'models' folder in dbt project, but not found: {str(self.models_path)}"
            )

        self.dbt_project_yml_path = self.dbt_project_path / "dbt_project.yml"

        if not self.dbt_project_yml_path.is_file():
            raise FileNotFoundError(
                f"Expected 'dbt_project.yml' config in dbt project, but not found: {str(self.dbt_project_yml_path)}"
            )

        self.default_schema = "dbt"

        dbt_project_raw_yml = self.dbt_project_yml_path.read_text(encoding="utf-8")
        self.dbt_project_conf = yaml.safe_load(dbt_project_raw_yml)

        self.PM = DBTPhysicalModel(version)

        if isinstance(source_paths, (str, Path)):
            raise TypeError("source_paths must be a list of paths, not a single path")
        if isinstance(ignore, str):
            raise TypeError("ignore must be a list of patterns, not a single string")

        self.source_paths = [Path(source_path) for source_path in source_paths or ()]
        for source_path in self.source_paths:
            if not source_path.exists():
                raise FileNotFoundError(f"dbt source path not found: {source_path}")

        self.ignore_spec = pathspec.GitIgnoreSpec.from_lines(ignore or ())

    def _is_ignored(self, path: Path) -> bool:
        """Return whether a file inside the dbt project matches an ignore pattern.

        :param path: File path under the dbt project directory.
        :type path: Path
        :returns: ``True`` when the file must not be parsed.
        :rtype: bool
        """
        try:
            relative_path = path.relative_to(self.dbt_project_path)
        except ValueError:
            return False
        return self.ignore_spec.match_file(relative_path.as_posix())

    def _files(self, folder: Path, pattern: str, recursive: bool = True) -> list[Path]:
        """Return the files in ``folder`` matching ``pattern``, without ignored ones.

        :param folder: Directory to search. A missing directory yields no files.
        :type folder: Path
        :param pattern: Glob pattern, e.g. ``*.yml``.
        :type pattern: str
        :param recursive: Whether to search subdirectories.
        :type recursive: bool
        :returns: Sorted file paths.
        :rtype: list[Path]
        """
        found = folder.rglob(pattern) if recursive else folder.glob(pattern)
        return sorted(path for path in found if not self._is_ignored(path))

    def _source_yml_files(self) -> list[Path]:
        """Return source YAML files: ``models/*.yml`` followed by ``source_paths``.

        :returns: File paths to parse as dbt source definitions.
        :rtype: list[Path]
        """
        files = self._files(self.models_path, "*.yml", recursive=False)
        for source_path in self.source_paths:
            if source_path.is_dir():
                files.extend(self._files(source_path, "*.yml"))
            elif not self._is_ignored(source_path):
                files.append(source_path)
        return files

    def _register_columns(
        self, table: Table, columns: list[dict] | None, yml_path: Path
    ) -> None:
        """Register the columns of a table described in YAML.

        Missing ``data_type`` and ``description`` are stored as empty strings.
        Columns without ``data_type`` are reported as a warning.

        :param table: Table owning the columns.
        :type table: Table
        :param columns: Column definitions from the YAML document.
        :type columns: list[dict] | None
        :param yml_path: YAML file the columns come from, used in messages.
        :type yml_path: Path
        """
        missing_data_type = []

        for column in columns or []:
            column_name = str(column["name"]).strip()
            data_type = column.get("data_type")
            if data_type is None:
                missing_data_type.append(column_name)

            column_nk = f"{table.nk}.{column_name}"

            col_obj = Column(
                id=id_generator(column_nk),
                nk=column_nk,
                layer_id=table.layer_id,
                table_id=table.id,
                name=column_name,
                data_type="" if data_type is None else str(data_type),
                description=str(column.get("description") or ""),
            )

            if col_obj.id not in self.PM.all_units_by_id:
                self.PM.register_column(col_obj)

        if missing_data_type:
            logger.warning(
                f"{yml_path}: {table.nk} has columns without data_type: "
                f"{', '.join(missing_data_type)}"
            )

    def _parse_source_model_yml(self, source_yml_path: Path) -> None:
        raw = source_yml_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw) or {}

        sources = doc.get("sources") or []
        if not isinstance(sources, list):
            return

        for source in sources:
            source_name = source["name"]

            # 1) Layer for the source
            layer_nk = source_name
            layer_obj = Layer(
                id=id_generator(layer_nk),
                nk=layer_nk,
                name=source_name,
                is_landing=True,
            )

            self.PM.register_layer(layer_obj)

            for table in source.get("tables") or []:
                # 2) Table
                table_nk = f"{source_name}.{table['name']}"
                table_obj = Table(
                    id=id_generator(table_nk),
                    nk=table_nk,
                    layer_id=layer_obj.id,
                    name=table["name"],
                )

                self.PM.register_table(table_obj)
                self.PM.all_tables_by_nk[table_nk] = table_obj

                # 3) Columns
                self._register_columns(table_obj, table.get("columns"), source_yml_path)

    def _parse_model_yml(self, model_yml_path: Path, layer_id: str) -> None:
        raw = model_yml_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw) or {}

        models = doc.get("models") or []

        for model in models:
            model_name = model["name"].strip()

            # 1) Ensure table exists
            table_nk = self.PM.all_units_by_id[layer_id].name + "." + model_name

            table_obj = Table(
                id=id_generator(table_nk),
                nk=table_nk,
                layer_id=layer_id,
                name=model_name,
            )

            self.PM.register_table(table_obj)
            self.PM.all_tables_by_nk[table_nk] = table_obj
            self.PM.all_dbt_tables_by_model[model_yml_path.stem] = table_obj

            # 2) Parse columns
            self._register_columns(table_obj, model.get("columns"), model_yml_path)

    def _parse_seed_yml(self, seed_yml_path: Path, layer_id: str) -> None:
        raw = seed_yml_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw) or {}

        seeds = doc.get("seeds") or []

        for seed in seeds:
            seed_name = seed["name"].strip()

            # 1) Ensure table exists
            table_nk = self.default_schema + "." + seed_name

            table_obj = Table(
                id=id_generator(table_nk),
                nk=table_nk,
                layer_id=layer_id,
                name=seed_name,
            )

            self.PM.register_table(table_obj)
            self.PM.all_tables_by_nk[table_nk] = table_obj
            self.PM.all_dbt_tables_by_model[seed_yml_path.stem] = table_obj

            # 2) Parse columns
            self._register_columns(table_obj, seed.get("columns"), seed_yml_path)

    def _parse_model_sql(
        self, model_name: str, model_sql_path: Path, layer_name: str
    ) -> None:
        """
        Register dependency nks found in SQL via ref()/source().
        """
        dependent = self.PM.all_tables_by_nk.get(f"{layer_name}.{model_name}")
        if not isinstance(dependent, Table):
            raise Exception(
                f"No model YAML registers {layer_name}.{model_name} ({model_sql_path}). "
                "Document the model, or ignore its .yml and .sql together."
            )

        text = model_sql_path.read_text(encoding="utf-8")

        for m in _REF_RE.finditer(text):
            table_name = m.group("table_name")
            schema_or_package_name = m.group("schema_name")
            table_obj = None

            if schema_or_package_name:
                table_obj = self.PM.all_tables_by_nk.get(
                    f"{schema_or_package_name}.{table_name}"
                )
            elif not schema_or_package_name and table_name:
                table_obj = self.PM.all_dbt_tables_by_model.get(table_name)
            else:
                raise Exception(f"Unknown model reference in {str(model_sql_path)}")

            if isinstance(table_obj, Table):
                self.PM.register_dependency(dependent, table_obj)
            else:
                logger.warning(
                    f"Could not resolve ref to table '{table_name}' in {str(model_sql_path)}. This may lead to missing dependencies in the physical model."
                )

        for m in _SOURCE_RE.finditer(text):
            table_name = m.group("table_name")
            schema_name = m.group("schema_name")
            table_nk = schema_name + "." + table_name
            table_obj = self.PM.all_tables_by_nk.get(table_nk)
            if isinstance(table_obj, Table):
                self.PM.register_dependency(dependent, table_obj)

    def parse_pm(self) -> PhysicalModel:
        # 0) parse models into registry
        # 1) parse source definitions
        for source_yml_path in self._source_yml_files():
            self._parse_source_model_yml(source_yml_path)

        layer_obj = Layer(
            id=id_generator(self.default_schema),
            nk=self.default_schema,
            name=self.default_schema,
            is_landing=False,
        )

        self.PM.register_layer(layer_obj)

        for seed_yml_file in self._files(self.seeds_path, "*.yml", recursive=False):
            self._parse_seed_yml(seed_yml_file, layer_obj.id)

        # 2) parse model definitions
        for project in self.dbt_project_conf["models"]:
            if "+" in project:
                continue
            for layer_name in self.dbt_project_conf["models"][project]:
                layer_obj = Layer(
                    id=id_generator(layer_name),
                    nk=layer_name,
                    name=layer_name,
                    is_landing=False,
                )

                self.PM.register_layer(layer_obj)

                layer_folder_path = self.models_path / layer_name

                for model_yml_file in self._files(layer_folder_path, "*.yml"):
                    self._parse_model_yml(model_yml_file, layer_id=layer_obj.id)

        # 2) SQL second
        for project in self.dbt_project_conf["models"]:
            if "+" in project:
                continue
            for layer_name in self.dbt_project_conf["models"][project]:
                layer_folder_path = self.models_path / layer_name
                for sql_path in self._files(layer_folder_path, "*.sql"):
                    self._parse_model_sql(sql_path.stem, sql_path, layer_name)

        return self.PM
