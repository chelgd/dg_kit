## dbt Integration

Parses a dbt project into a `PhysicalModel` with layers, tables, columns, and dependencies.

This integration is useful for extracting governance metadata from dbt and feeding it into
CI checks, documentation, or data catalog syncs.

## Requirements
- A dbt project directory with `dbt_project.yml`
- A `models/` directory containing model `.yml` and `.sql` files

## Usage
```python
from dg_kit.integrations.dbt.parser import DBTParser

pm = DBTParser("path/to/dbt_project").parse_pm()

print(pm.version, len(pm.layers), len(pm.tables))
```

## What It Parses
- Sources defined in top-level `models/*.yml`
- Models and columns from layer `models/<layer>/*.yml`
- Dependencies from `ref()` and `source()` calls in `models/**/*.sql`

## Notes
- Dependencies are registered only when referenced models/sources exist in the parsed metadata.
