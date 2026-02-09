from __future__ import annotations

import re
from pathlib import Path

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


class DBTPhysicalModel(PhysicalModel):
    def __init__(self, version: str):
        super().__init__(version)
        self.all_tables_by_nk: dict[str, Table] = {}


class DBTParser:
    def __init__(
        self,
        dbt_project_path: Path,
        version: str,
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
                natural_key=layer_nk,
                name=source_name,
                is_landing=True,
            )

            self.PM.register_layer(layer_obj)

            for table in source["tables"]:
                # 2) Table
                table_nk = f"{source_name}.{table['name']}"
                table_obj = Table(
                    id=id_generator(table_nk),
                    natural_key=table_nk,
                    layer_id=layer_obj.id,
                    name=table["name"],
                )

                self.PM.register_table(table_obj)
                self.PM.all_tables_by_nk[table_nk] = table_obj

                # 3) Columns
                for column in table["columns"]:
                    col_name = column["name"]
                    data_type = column["data_type"]
                    description = column["description"]
                    col_nk = f"{table_nk}.{col_name}"

                    col_obj = Column(
                        id=id_generator(col_nk),
                        natural_key=col_nk,
                        layer_id=layer_obj.id,
                        table_id=table_obj.id,
                        name=str(col_name),
                        data_type=str(data_type),
                        description=str(description),
                    )

                    if col_obj.id not in self.PM.all_units_by_id:
                        self.PM.register_column(col_obj)

    def _parse_model_yml(self, model_yml_path: Path, layer_id: str) -> None:
        raw = model_yml_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw)

        models = doc["models"]

        for model in models:
            model_name = model["name"].strip()

            # 1) Ensure table exists
            table_nk = self.PM.all_units_by_id[layer_id].name + "." + model_name

            table_obj = Table(
                id=id_generator(table_nk),
                natural_key=table_nk,
                layer_id=layer_id,
                name=model_name,
            )

            self.PM.register_table(table_obj)
            self.PM.all_tables_by_nk[table_nk] = table_obj

            # 2) Parse columns
            columns = model["columns"]

            for column in columns:
                column_name = column["name"].strip()
                description = column["description"]
                data_type = column["data_type"]

                column_nk = f"{table_nk}.{column_name}"

                col_obj = Column(
                    id=id_generator(column_nk),
                    natural_key=column_nk,
                    layer_id=layer_id,
                    table_id=table_obj.id,
                    name=column_name,
                    data_type=str(data_type),
                    description=str(description),
                )

                if col_obj.id not in self.PM.all_units_by_id:
                    self.PM.register_column(col_obj)

    def _parse_seed_yml(self, seed_yml_path: Path, layer_id: str) -> None:
        raw = seed_yml_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw)

        seeds = doc["seeds"]

        for seed in seeds:
            seed_name = seed["name"].strip()

            # 1) Ensure table exists
            table_nk = self.default_schema + "." + seed_name

            table_obj = Table(
                id=id_generator(table_nk),
                natural_key=table_nk,
                layer_id=layer_id,
                name=seed_name,
            )

            self.PM.register_table(table_obj)
            self.PM.all_tables_by_nk[table_nk] = table_obj

            # 2) Parse columns
            columns = seed["columns"]

            for column in columns:
                column_name = column["name"].strip()
                description = column["description"]
                data_type = column["data_type"]

                column_nk = f"{table_nk}.{column_name}"

                col_obj = Column(
                    id=id_generator(column_nk),
                    natural_key=column_nk,
                    layer_id=layer_id,
                    table_id=table_obj.id,
                    name=column_name,
                    data_type=str(data_type),
                    description=str(description),
                )

                if col_obj.id not in self.PM.all_units_by_id:
                    self.PM.register_column(col_obj)

    def _parse_model_sql(
        self, model_name: str, model_sql_path: Path, layer_name: str
    ) -> None:
        """
        Register dependency natural_keys found in SQL via ref()/source().
        """
        text = model_sql_path.read_text(encoding="utf-8")

        for m in _REF_RE.finditer(text):
            table_name = m.group("table_name")
            schema_name = m.group("schema_name")
            table_nk = schema_name + "." + table_name if schema_name else table_name
            table_obj = self.PM.all_tables_by_nk.get(table_nk)
            if isinstance(table_obj, Table):
                self.PM.register_dependency(
                    self.PM.all_tables_by_nk[layer_name + "." + model_name], table_obj
                )

        for m in _SOURCE_RE.finditer(text):
            table_name = m.group("table_name")
            schema_name = m.group("schema_name")
            table_nk = schema_name + "." + table_name
            table_obj = self.PM.all_tables_by_nk.get(table_nk)
            if isinstance(table_obj, Table):
                self.PM.register_dependency(
                    self.PM.all_tables_by_nk[layer_name + "." + model_name], table_obj
                )

    def parse_pm(self) -> PhysicalModel:
        # 1) parse source definitions
        for source_yml_path in self.models_path.glob("*.yml"):
            self._parse_source_model_yml(source_yml_path)

        layer_obj = Layer(
            id=id_generator(self.default_schema),
            natural_key=self.default_schema,
            name=self.default_schema,
            is_landing=False,
        )
        self.PM.register_layer(layer_obj)

        for seed_yml_file in self.seeds_path.glob("*.yml"):
            self._parse_seed_yml(seed_yml_file, layer_obj.id)

        # 2) parse model definitions
        for project in self.dbt_project_conf["models"]:
            for layer_name in self.dbt_project_conf["models"][project]:
                layer_obj = Layer(
                    id=id_generator(layer_name),
                    natural_key=layer_name,
                    name=layer_name,
                    is_landing=False,
                )

                self.PM.register_layer(layer_obj)

                layer_folder_path = self.models_path / layer_name

                for model_yml_file in layer_folder_path.rglob("*.yml"):
                    self._parse_model_yml(model_yml_file, layer_id=layer_obj.id)

        # 2) SQL second
        for project in self.dbt_project_conf["models"]:
            for layer_name in self.dbt_project_conf["models"][project]:
                layer_folder_path = self.models_path / layer_name
                for sql_path in layer_folder_path.rglob("*.sql"):
                    self._parse_model_sql(sql_path.stem, sql_path, layer_name)

        return self.PM
