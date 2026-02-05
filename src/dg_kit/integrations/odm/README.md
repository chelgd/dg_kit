## Oracle Data Modeler Integration

Parses Oracle Data Modeler (ODM) project exports and converts them into `dg_kit` core objects:
- Logical Model (`LogicalModel`)
- Business Information (`BusinessInformation`)

This integration is useful for extracting governance metadata from ODM and using it in CI checks, data catalog sync, or internal tooling.

## Requirements
- Oracle Data Modeler project in `.dmd` format
- The `.dmd` file must sit next to a folder with the same base name that contains the exported assets (ODM’s standard structure)

Expected layout:
```
MyModel.dmd
MyModel/
  logical/
  businessinfo/
```

## Usage
```python
from dg_kit.integrations.odm.parser import ODMParser

parser = ODMParser("path/to/MyModel.dmd")

bi = parser.parse_bi()
lm = parser.parse_lm()

print(lm.version, len(lm.entities))
```

## Versioned Projects
If you keep multiple `.dmd` files in a folder (one per version), use `ODMVersionedProjectParser`:
```python
from dg_kit.integrations.odm.parser import ODMVersionedProjectParser

parser = ODMVersionedProjectParser("path/to/odm_versions_folder")
model = parser.get_model("MyModel")
bi = parser.get_bi("MyModel")
```

## Notes
- Business information includes documents, contacts, teams, emails, and URLs extracted from ODM.
- Logical model entities, attributes, and relations are built from ODM XML assets.
- Dynamic ODM properties are used for fields like `domain`, `pm_map`, and `master_source_systems`.
