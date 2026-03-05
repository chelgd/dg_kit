# Data Governance Kit (`dg_kit`)

`dg_kit` provides programmatic access to governance metadata across logical models,
physical models, and data catalogs. It is designed for CI checks, governance
automation, and metadata synchronization workflows.

## What it supports

- Parse physical metadata from dbt projects.
- Parse logical and business metadata from Oracle Data Modeler exports.
- Validate model consistency with YAML-driven convention rules.
- Synchronize a data catalog with a Notion data source.

## Requirements

- Python `>=3.10`

## Installation

Install the package in editable mode:

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dbt]"
pip install -e ".[notion]"
```

If you use `uv`:

```bash
uv sync --group dev
```

## CLI usage

The package exposes a CLI entrypoint:

```bash
dg_kit <command> --config ./dg_kit.yml
```

Supported commands:

- `test` validates LM/PM consistency and convention rules.
- `sync` syncs the local model to the remote data catalog.
- `pull` pulls the remote data catalog into a local checkpoint.

### Environment variables (for `sync` and `pull`)

These commands require:

```bash
export NOTION_TOKEN=...
export DATA_CATALOG_ID=...
```

On PowerShell:

```powershell
$env:NOTION_TOKEN="..."
$env:DATA_CATALOG_ID="..."
```

### Example commands

```bash
dg_kit test --config ./dg_kit.yml --convention ./dg_kit.convention.yml
dg_kit sync --config ./dg_kit.yml
dg_kit pull --config ./dg_kit.yml
```

## Configuration examples

`dg_kit.yml`:

```yaml
name: sample_project
version: v1
logical_model:
  path: ./metadata/odm_versions
physical_model:
  path: ./warehouse/dbt_project
data_catalog:
  dc_checkpoint_path: ./.artifacts
  row_property_mapping:
    id: ID
    title: Name
    type: Type
    domain: Domain
  section_name_mapping:
    description: Description
    pk_attributes_references: PK attributes
    attributes_references: Attributes
    relations_references: Relations
    linked_documents: Linked documents
    responsible_parties: Responsible parties
    pm_mapping_references: Physical mapping
    source_systems: Source systems
    parent_entity_reference: Parent entity
    data_type: Data type
    sensitivity_type: Sensitivity type
    source_entity_reference: Source entity
    target_entity_reference: Target entity
```

`dg_kit.convention.yml`:

```yaml
lm_mapping_layers:
  - core
rules:
  lm_x_pm_consistency:
    severity: error
    description: Logical and physical mappings must stay consistent.
  allowed_dependencies:
    severity: warning
    description: Restrict cross-layer dependencies.
    rules:
      core: [stage, core]
  regex_by_layer:
    severity: warning
    description: Enforce table naming conventions.
    rules:
      core_tables:
        layer: core
        regex:
          string: "^core_[a-z0-9_]+$"
technical_fields:
  core:
    - created_at
    - updated_at
```

## Python API quick examples

Build physical model from dbt:

```python
from pathlib import Path
from dg_kit.integrations.dbt.parser import DBTParser

pm = DBTParser(Path("path/to/dbt_project"), version="v1").parse_pm()
print(pm.version, len(pm.tables))
```

Parse one ODM version from a versioned project directory:

```python
from pathlib import Path
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser

parser = ODMVersionedProjectParser(Path("path/to/odm_versions"))
parser.parse_version("v1", pm)
lm = parser.get_model("v1")
print(lm.version, len(lm.entities))
```

## Development

Run local quality checks:

```bash
./scripts/ci.sh
```

Run tests:

```bash
pytest
```
