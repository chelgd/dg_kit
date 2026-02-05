## Notion Integration

Syncs Data Governance objects to a Notion data source (database) and keeps properties and page bodies in sync.

This integration is useful for pushing logical and physical model details into a shared catalog space
where teams can browse governance metadata.

## Requirements
- A Notion integration token
- A Notion data source (database) ID
- Proper access granted to the data source for the integration

## Usage
```python
from dg_kit.integrations.notion.api import NotionDataCatalog

catalog = NotionDataCatalog(
    notion_token="secret",
    dc_table_id="data_source_id",
)

rows = catalog.pull()
print(len(rows))
```

## Properties Expected
By default, the Notion database should contain the following properties:
- `Data unit` (title)
- `Data unit type` (select)
- `Data unit uuid` (rich text)
- `Domain` (select)

Property names can be overridden when constructing `NotionDataCatalog`.

## Notes
- `update_page_by_uuid` rewrites page blocks to reflect the latest entity/attribute/relation details.
- `update_properties_by_uuid` updates the Notion properties only.
- `add_data_unit` creates a new page if the external UUID does not exist.
