# Data Models

All models are Pydantic `BaseModel` classes defined in `extract_zip_flow_with_folder_structure.py`.

---

## `ParentData`

Represents the parent relationship and folder flag for a single zip entry. Defined in this file but **not actively used** by the current flow logic — it is a carry-over from the base `extract_zip_flow.py`.

```python
class ParentData(BaseModel):
    parent: Optional[int] = None
    isFolder: bool
```

| Field      | Type            | Description |
|------------|-----------------|-------------|
| `parent`   | `Optional[int]` | Index of the parent entry in the file list. |
| `isFolder` | `bool`          | `True` if entry is a folder (path ends with `/`). |

---

## `ItemsAndParentsDataResponse`

Groups item schemas with their parent relationship data. Defined in this file but **not actively used** by the current flow logic — carry-over from the base flow.

```python
class ItemsAndParentsDataResponse(BaseModel):
    items_data: List[NewItemSchema]
    parents_data: List[ParentData]
```

| Field          | Type                  | Description |
|----------------|-----------------------|-------------|
| `items_data`   | `List[NewItemSchema]` | Item records. |
| `parents_data` | `List[ParentData]`    | Corresponding parent data per item. |

> These two models are unused in the current flow. They may be referenced if the flow is extended to also insert items/files into the dashboard database.

---

## `PrepareExtractionResponse`

Output of the `prepare_extraction` task. Contains all path and key information needed by downstream tasks.

```python
class PrepareExtractionResponse(BaseModel):
    file_download_path: str
    file_extraction_path: str
    item_title: str
    file_s3_key: str
```

| Field                  | Type  | Description | Example |
|------------------------|-------|-------------|---------|
| `file_download_path`   | `str` | Full local path where the zip will be saved. | `./work_dir/abc-123/my_workflow.zip` |
| `file_extraction_path` | `str` | Local directory where the zip will be extracted. | `./work_dir/abc-123` |
| `item_title`           | `str` | Display name with file extension stripped. | `my_workflow` |
| `file_s3_key`          | `str` | S3 object key of the zip file. | `my_workflow.zip` |

> `file_download_path` = `file_extraction_path` + `/` + `file_s3_key`. The zip lands inside the same unique folder it will be extracted into.
