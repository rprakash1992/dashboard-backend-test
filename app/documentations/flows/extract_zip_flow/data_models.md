# Data Models

All models are Pydantic `BaseModel` classes defined in `extract_zip_flow.py`.

---

## `ParentData`

Represents the parent relationship and type of a single entry in the zip file list.

```python
class ParentData(BaseModel):
    parent: Optional[int] = None
    isFolder: bool
```

| Field      | Type            | Description |
|------------|-----------------|-------------|
| `parent`   | `Optional[int]` | Index of the parent entry in the file list. `None` for the root entry. |
| `isFolder` | `bool`          | `True` if this entry is a folder (zip path ends with `/`). |

**Examples:**

| Scenario | `parent` | `isFolder` |
|---|---|---|
| Root folder (`project/`) | `None` | `True` |
| Subfolder inside root (`project/folder1/`) | `0` | `True` |
| File inside root (`project/file.txt`) | `0` | `False` |
| File inside subfolder (`project/folder1/a.vcp`) | `1` | `False` |

---

## `ItemsAndParentsDataResponse`

Output of `get_items_titles_and_parents_data`. Pairs display titles with parent relationship data for every entry in the file list.

```python
class ItemsAndParentsDataResponse(BaseModel):
    items_titles: List[str]
    parents_data: List[ParentData]
```

| Field          | Type               | Description |
|----------------|--------------------|-------------|
| `items_titles` | `List[str]`        | Display name for each entry. The root always takes the user-facing `file_title`. |
| `parents_data` | `List[ParentData]` | One `ParentData` per entry, in the same order as the file list. |

**Example:**

Given a zip named `project.zip` containing `folder1/` and `folder1/design.vcp`:

```python
ItemsAndParentsDataResponse(
    items_titles=["project", "folder1", "design.vcp"],
    parents_data=[
        ParentData(parent=None, isFolder=True),   # project/
        ParentData(parent=0,    isFolder=True),   # project/folder1/
        ParentData(parent=1,    isFolder=False),  # project/folder1/design.vcp
    ]
)
```

---

## `PrepareExtractionResponse`

Output of the `prepare_extraction` task. Contains all path and key information needed by the rest of the flow.

```python
class PrepareExtractionResponse(BaseModel):
    file_download_path: str
    file_extraction_path: str
    item_title: str
    file_s3_key: str
```

| Field                  | Type  | Description | Example |
|------------------------|-------|-------------|---------|
| `file_download_path`   | `str` | Full local path where the zip will be saved. | `./work_dir/abc-123/report.zip` |
| `file_extraction_path` | `str` | Local directory where the zip will be extracted. | `./work_dir/abc-123` |
| `item_title`           | `str` | Display name for the root folder (file extension stripped). | `report` |
| `file_s3_key`          | `str` | S3 object key of the zip file. | `report.zip` |

> **Note:** `file_download_path` is `file_extraction_path` + `/` + `file_s3_key`. The zip lands inside the same unique folder that it will be extracted into.
