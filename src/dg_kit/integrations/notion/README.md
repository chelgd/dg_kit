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

catalog.pull_data_catalog()
row = catalog.get_row_by_id("data-unit-id")
page = catalog.get_page_by_id("data-unit-id")
print(row, page)
```

## Properties Expected
By default, the Notion database should contain the following properties:
- `Data unit` (title)
- `Data unit type` (select)
- `Data unit uuid` (rich text)
- `Domain` (select)

Property names can be overridden when constructing `NotionDataCatalog`.

## Notes
- `pull_data_catalog` reads the Notion data source and parses page bodies into `Entity`, `Attribute`, and `Relation`.
- `update_page_by_id` rewrites page blocks to reflect the latest entity/attribute/relation details.
- `update_row_by_id` updates the Notion properties only.
- `add_row` creates a new page if the external UUID does not exist.
- Parsing logic lives in `src/dg_kit/integrations/notion/parser.py`.
