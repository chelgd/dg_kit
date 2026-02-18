from __future__ import annotations

from typing import Any


from sys import path
from pathlib import Path
import yaml
from os import environ
from dg_kit.integrations.dbt.parser import DBTParser
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser
from dg_kit.base.convention import ConventionValidator
from dg_kit.base.data_catalog import DataCatalog
from dg_kit.integrations.notion.api import NotionDataCatalog



def run(config: dict[str, Any]) -> None:
    current_version = config.get("current_model", {}).get("version")
    odm_project_path = Path(config.get("current_model", {}).get("odm_path"))
    print(f'odm_project_path : {odm_project_path}')
    dbt_project_path = Path(config.get("current_model", {}).get("dbt_path"))
    print(f'dbt_project_path : {dbt_project_path}')
    new_version = config.get("new_model", {}).get("version")

    print(f"current_model.version={current_version}")
    print(f"new_model.version={new_version}")


    odm_project = ODMVersionedProjectParser(odm_project_path=odm_project_path)
    dbt_parser = DBTParser(dbt_project_path, config['new_model']['version'])

    PM = dbt_parser.parse_pm()
    odm_project.parse_version(config['new_model']['version'], PM)
    LM = odm_project.get_model(config['new_model']['version'])
    BI = odm_project.get_bi(config['new_model']['version'])

    notion_config = {
        'row_property_mapping': {
            'id': 'Data unit id',
            'title': 'Data unit',
            'type': 'Data unit type',
            'domain': 'Domain',
        },
        'section_name_mapping': {
            'description': 'Description:',
            'pk_attributes_references': 'Primary Key attributes:',
            'attributes_references': 'Attributes:',
            'relations_references': 'Relations:',
            'linked_documents': 'Linked docs:',
            'responsible_parties': 'Responsible parties:',
            'source_systems': 'Master source systems:',
            'pm_mapping_references': 'Core layer map:',
            'parent_entity_reference': 'Parent entity:',
            'data_type': 'Data type:',
            'sensitivity_type': 'Sensetivity type:',
            'source_entity_reference': 'Source entity:',
            'target_entity_reference': 'Target entity:',

        },
    }

    ndc_engine = NotionDataCatalog(
        notion_token=environ["NOTION_TOKEN"],
        dc_table_id=environ["DATA_CATALOG_ID"],
        notion_config=notion_config,
    )

    dg = DataCatalog(
        LM=LM,
        PM=PM,
        BI=BI,
        engine=ndc_engine
    )

    #convention_validator = ConventionValidator(
    #    LM,
    #    PM,
    #    convention
    #)
    #convention_breaches = convention_validator.validate()
    #for convention_breah in convention_breaches:
    #    print(convention_breah.message)


    for id, unit in LM.all_units_by_id.items():
        if not unit.pm_map:
            print(f"Missing PM mapping for {unit.name}")
            continue

    for table in PM.tables.values():
        layer_name = PM.layers[table.layer_id].name
        if layer_name == 'core' and table.id not in dg.lm_objects_by_pm_id:
            print(f"This PM object is not used in LM: {layer_name + '.' + table.name}")


    #for column in PM.columns.values():
    #    layer_name = PM.layers[column.layer_id].name
    #    table_name = PM.tables[column.table_id].name
    #    if layer_name == 'core' and column.id not in dg.lm_objects_by_pm_id and column.name not in TECH_FIELDS_BY_LAYER[layer_name]:
    #        print(f"This PM object is not used in LM: {layer_name + '.' + table_name + '.' + column.name}")


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
