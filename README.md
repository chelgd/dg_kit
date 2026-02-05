## Data Governance Kit (dg_kit)

Data Governance Kit helps you access Data Governance information programmatically.
It provides core objects that model Physical Model, Logical Model, Business Information,
and related governance metadata. Integrations let you pull this data from tools like
dbt, Oracle Data Modeler, and Notion, with more connectors planned in upcoming releases.

This toolkit is handy for building Data Governance CI gates, strengthening Data Ops
practices, and keeping governance checks close to your delivery workflows.

## Requirements
- Python >= 3.10

## Install
```bash
pip install -e .
```

Optional extras:
```bash
pip install -e ".[dbt]"
pip install -e ".[notion]"
```

## Quick Start

### Parse an Oracle Data Modeler project
```python
from dg_kit.integrations.odm.parser import ODMParser

parser = ODMParser("path/to/model.dmd")
bi = parser.parse_bi()
lm = parser.parse_lm()

print(lm.version, len(lm.entities))
```

### Parse a dbt project into a physical model
```python
from dg_kit.integrations.dbt.parser import DBTParser

pm = DBTParser("path/to/dbt_project").parse_pm()
print(pm.version, len(pm.tables))
```

### Validate with conventions
```python
from dg_kit.base.convention import Convention, ConventionValidator
from dg_kit.base.enums import ConventionRuleSeverity

convention = Convention("example")

@convention.rule(
    name="has-entities",
    severity=ConventionRuleSeverity.ERROR,
    description="Logical model must contain at least one entity",
)
def has_entities(lm, pm):
    return set() if lm.entities else {("no entities")}

issues = ConventionValidator(lm, pm, convention).validate()
```

### Sync to Notion data catalog
```python
from dg_kit.integrations.notion.api import NotionDataCatalog

catalog = NotionDataCatalog(
    notion_token="secret",
    dc_table_id="data_source_id",
)
rows = catalog.pull()
print(len(rows))
```

## Development
Run tests:
```bash
pytest
```

Export requirements with uv:
```bash
uv export --extra dbt --extra notion --group test -o requirements.txt
```
