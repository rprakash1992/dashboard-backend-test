# Helper Functions

These are plain Python functions (no Prefect `@task` decoration). They are called internally by the `update_database_records` task to build the data structures needed before inserting into the database.

---

## `remove_slash(file_name)`

Extracts the display name from a zip entry path by removing leading path segments and trailing slashes.

### Logic

| Condition | Action |
|---|---|
| Path ends with `/` (folder) | Return the segment just before the trailing slash |
| Path contains `/` but does not end with `/` (file) | Return the segment after the last `/` |
| Path has no `/` (top-level entry) | Return unchanged |

### Examples

| Input | Output |
|---|---|
| `"folder1/"` | `"folder1"` |
| `"folder1/file.txt"` | `"file.txt"` |
| `"folder1/subfolder/"` | `"subfolder"` |
| `"folder1/subfolder/a.vcp"` | `"a.vcp"` |
| `"standalone.txt"` | `"standalone.txt"` |

---

## `get_index_of_parent(file_list, file)`

Given the full file list and a single entry path, returns the list index of that entry's parent folder.

### Logic

1. If the path has no `/` → it's a root-level item, returns `0`.
2. If the path is nested:
   - For a folder path (ends with `/`): strip the trailing slash, then take everything up to and including the next-to-last `/` to get the parent path.
   - For a file path: take everything up to and including the last `/` to get the parent path.
   - Look up that parent path in `file_list` using `.index()`.
3. If the parent path is not found → returns `-1`.

### Examples

Given:
```python
file_list = [
    "report/",                          # index 0
    "report/folder1/",                  # index 1
    "report/folder1/file.txt",          # index 2
    "report/folder1/subfolder/",        # index 3
    "report/folder1/subfolder/a.vcp",   # index 4
]
```

| `file` | Parent path looked up | Returns |
|---|---|---|
| `"report/"` | `""` (no parent) | `0` |
| `"report/folder1/"` | `"report/"` | `0` |
| `"report/folder1/file.txt"` | `"report/folder1/"` | `1` |
| `"report/folder1/subfolder/"` | `"report/folder1/"` | `1` |
| `"report/folder1/subfolder/a.vcp"` | `"report/folder1/subfolder/"` | `3` |

---

## `get_items_titles_and_parents_data(file_list, file_title)`

Processes the full file list and produces display titles and parent relationships for every entry. This is the main orchestrator of the two helpers above.

The first entry is always the root folder and receives `file_title` as its display name. All subsequent entries derive their display name from `remove_slash`.

### Inputs

| Parameter    | Type        | Description |
|--------------|-------------|-------------|
| `file_list`  | `List[str]` | Full list of zip paths, with the root folder prepended (e.g. `["project/", "project/folder1/", ...]`). |
| `file_title` | `str`       | Display name for the root folder (zip name without extension). |

### Returns

[`ItemsAndParentsDataResponse`](data_models.md#itemsandparentsdataresponse)

### Example

**Input:**
```python
file_list = [
    "report/",
    "report/folder1/",
    "report/folder1/file.txt",
    "report/folder1/subfolder/",
    "report/folder1/subfolder/a.vcp",
]
file_title = "report"
```

**Output:**
```python
ItemsAndParentsDataResponse(
    items_titles=["report", "folder1", "file.txt", "subfolder", "a.vcp"],
    parents_data=[
        ParentData(parent=None, isFolder=True),   # report/
        ParentData(parent=0,    isFolder=True),   # report/folder1/
        ParentData(parent=1,    isFolder=False),  # report/folder1/file.txt
        ParentData(parent=1,    isFolder=True),   # report/folder1/subfolder/
        ParentData(parent=3,    isFolder=False),  # report/folder1/subfolder/a.vcp
    ]
)
```

---

## `get_files_data(items_titles, file_list, parents_data)`

Builds a list of file record dictionaries ready to be inserted into the database — one dict per entry.

### Rules

- **Folders** (`isFolder=True`): `url = ""`, `file_extension = "vcollab_folder"`.
- **Files** (`isFolder=False`): `url = "<uuid>.<ext>"` (UUID generated at call time), `file_extension = <ext>`.
- `parent` is always `None` here — it is set later by `update_files_parent`.

### Inputs

| Parameter      | Type               | Description |
|----------------|--------------------|-------------|
| `items_titles` | `List[str]`        | Display names from `get_items_titles_and_parents_data`. |
| `file_list`    | `List[str]`        | Full zip path list (used to detect folders and extract extensions). |
| `parents_data` | `List[ParentData]` | Used to check `isFolder` per entry. |

### Returns

`List[dict]` — one dict per entry with keys: `title`, `description`, `image`, `tags`, `file_extension`, `is_uploaded`, `parent`, `url`.

### Example

**Input:**
```python
items_titles = ["report", "folder1", "file.txt", "subfolder", "a.vcp"]
file_list    = ["report/", "report/folder1/", "report/folder1/file.txt",
                "report/folder1/subfolder/", "report/folder1/subfolder/a.vcp"]
parents_data = [ParentData(parent=None, isFolder=True), ...]
```

**Output:**
```python
[
    {"title": "report",    "url": "",            "file_extension": "vcollab_folder", "is_uploaded": True, "parent": None, "description": "", "image": "", "tags": []},
    {"title": "folder1",   "url": "",            "file_extension": "vcollab_folder", "is_uploaded": True, "parent": None, "description": "", "image": "", "tags": []},
    {"title": "file.txt",  "url": "uuid-1.txt",  "file_extension": "txt",            "is_uploaded": True, "parent": None, "description": "", "image": "", "tags": []},
    {"title": "subfolder", "url": "",            "file_extension": "vcollab_folder", "is_uploaded": True, "parent": None, "description": "", "image": "", "tags": []},
    {"title": "a.vcp",     "url": "uuid-2.vcp",  "file_extension": "vcp",            "is_uploaded": True, "parent": None, "description": "", "image": "", "tags": []},
]
```
