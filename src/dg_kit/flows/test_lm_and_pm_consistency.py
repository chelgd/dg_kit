from sys import path
from pathlib import Path
import yaml

from dg_kit.integrations.dbt.parser import DBTParser
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser
from dg_kit.base.convention import ConventionValidator
from dg_kit.base.data_catalog import DataCatalog, DataCatalogEngine

ci_path = Path(__file__).parent.parent
release_config_path = ci_path / 'release.yml'
data_model_path = Path(__file__).parent.parent.parent / 'data_model'
dbt_project_path = data_model_path / 'dbt'
odm_project_path = data_model_path / 'odm'

path.append(str(ci_path))

from model_convention import convention, TECH_FIELDS_BY_LAYER

release_config = yaml.safe_load(release_config_path.open())
odm_project = ODMVersionedProjectParser(odm_project_path=odm_project_path)
dbt_parser = DBTParser(dbt_project_path, release_config_path['new_model']['physical_model'])

PM = dbt_parser.parse_pm()
odm_project.parse_version(release_config_path['new_model']['logical_model'], PM)
LM = odm_project.get_model(release_config_path['new_model']['logical_model'])

dg = DataCatalog(
    LM=LM,
    PM=PM,
    engine=DataCatalogEngine
)

convention_validator = ConventionValidator(
    LM,
    PM,
    convention
)
convention_breaches = convention_validator.validate()
for convention_breah in convention_breaches:
    print(convention_breah.message)


for id, unit in LM.all_units_by_id.items():
    if not unit.pm_map:
        print(f"Missing PM mapping for {unit.name}")
        continue

for table in PM.tables.values():
    layer_name = PM.layers[table.layer_id].name
    if layer_name == 'core' and table.id not in dg.lm_objects_by_pm_id:
        print(f"This PM object is not used in LM: {layer_name + '.' + table.name}")


for column in PM.columns.values():
    layer_name = PM.layers[column.layer_id].name
    table_name = PM.tables[column.table_id].name
    if layer_name == 'core' and column.id not in dg.lm_objects_by_pm_id and column.name not in TECH_FIELDS_BY_LAYER[layer_name]:
        print(f"This PM object is not used in LM: {layer_name + '.' + table_name + '.' + column.name}")


for dependent_id, dependencies_set in PM.dependencies.items():
    for dependency_id in dependencies_set:
        dependent = PM.all_units_by_id[dependent_id]
        dependent_layer = PM.layers[dependent.layer_id]

        dependency = PM.all_units_by_id[dependency_id]
        dependency_layer = PM.layers[dependency.layer_id]

        if  dependent_layer.name == 'core' and dependency_layer.name != 'raw':
            print(f"{dependent.name} from core layer depends on {dependency.name} which is from {dependency_layer.name} layer")

        if  dependent_layer.name == 'raw' and not dependency_layer.is_landing:
            print(f"{dependent.name} from raw layer depends on {dependency.name} which is from {dependency_layer.name} layer")