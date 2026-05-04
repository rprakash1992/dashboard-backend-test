# Prefect Tasks

Each function below is decorated with `@task` and runs as a tracked step inside the `extract-zip-workflow` Prefect flow.

---

## `prepare_extraction` (async)

**Prefect task name:** `prepare-extraction`

Fetches the file and item records from the database for the input zip, generates a unique local working directory, and assembles all path/key information needed by downstream tasks.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `loggedin_user_id`      | `str` | ID of the requesting user. |
| `selected_workspace_id` | `str` | Workspace the zip item belongs to. |
| `input_item_id`         | `str` | DB item ID of the zip file to extract. |

### Steps

1. Opens a DB session and fetches the `FileSchema` for `input_item_id` to get `file.url` (the S3 key).
2. Generates a UUID and builds the unique local paths:
   - `unique_folder` = `./work_dir/<uuid>`
   - `file_download_path` = `./work_dir/<uuid>/<s3_key>`
   - `file_extraction_path` = `./work_dir/<uuid>`
3. Fetches the `ItemSchema` for `input_item_id` to get the display title.
4. Strips the file extension from the title (e.g. `"report.zip"` → `"report"`).
5. Returns a [`PrepareExtractionResponse`](data_models.md#prepareextractionresponse).

### Raises

`ValueError` if `file_s3_key` is empty or falsy.

### Returns

[`PrepareExtractionResponse`](data_models.md#prepareextractionresponse)

### Example

```python
# Input
input_item_id = "item-001"   # DB item for "report.zip"

# Output
PrepareExtractionResponse(
    file_s3_key         = "report.zip",
    file_download_path  = "./work_dir/f47ac10b/report.zip",
    file_extraction_path= "./work_dir/f47ac10b",
    item_title          = "report",
)
```

---

## `download_file_from_s3` (async)

**Prefect task name:** `download-from-s3`

Downloads the zip file from S3 to the local filesystem.

### Inputs

| Parameter       | Type  | Description |
|-----------------|-------|-------------|
| `file_s3_key`   | `str` | S3 object key of the zip file. |
| `download_path` | `str` | Full local path where the file will be saved. |

### Steps

1. Creates all parent directories for `download_path` if they don't exist (`os.makedirs`).
2. Calls `S3ClientService.download_file_to_local_path(file_s3_key, download_path)`.

### Example

```
file_s3_key   = "report.zip"
download_path = "./work_dir/f47ac10b/report.zip"

→ Creates ./work_dir/f47ac10b/ if it doesn't exist
→ Downloads S3:"report.zip" to ./work_dir/f47ac10b/report.zip
```

---

## `extract_zip_file` (sync)

**Prefect task name:** `extract-zip-file`

Extracts all contents of the downloaded zip file into the extraction directory.

### Inputs

| Parameter    | Type  | Description |
|--------------|-------|-------------|
| `zip_path`   | `str` | Local path to the `.zip` file. |
| `extract_to` | `str` | Local directory to extract files into. |

### Returns

`list[str]` — the zip's `namelist()`: relative internal paths of all entries (folders end with `/`).

> **Note:** The root folder itself is NOT in this list. It is prepended later in `update_database_records`.

### Example

```
zip_path   = "./work_dir/f47ac10b/report.zip"
extract_to = "./work_dir/f47ac10b"

→ Returns:
[
    "folder1/",
    "folder1/file.txt",
    "folder1/subfolder/",
    "folder1/subfolder/a.vcp",
]
```

---

## `update_database_records` (async)

**Prefect task name:** `update-database`

The core database task. Builds the full file list (with root prepended), computes parent relationships, inserts all new items/files into the database, then triggers `update_files_parent` to set FK references.

### Inputs

| Parameter               | Type        | Description |
|-------------------------|-------------|-------------|
| `loggedin_user_id`      | `str`       | User context. |
| `selected_workspace_id` | `str`       | Workspace context. |
| `item_title`            | `str`       | Root folder display name (e.g. `"report"`). |
| `output_item_id`        | `Any`       | DB item ID of the pre-existing root folder. |
| `file_list_extracted`   | `list[str]` | Raw zip namelist from `extract_zip_file`. |
| `extraction_path`       | `str`       | Local directory where files were extracted. |

### Steps

1. Prepends `"<item_title>/"` to `file_list_extracted` to form the full `file_list`.
2. Calls [`get_items_titles_and_parents_data`](helper_functions.md#get_items_titles_and_parents_datafile_list-file_title) to get titles and parent indices.
3. Fetches the pre-existing `output_item` and `output_file` from DB.
4. Calls [`get_files_data`](helper_functions.md#get_files_dataitems_titles-file_list-parents_data) to build insert dicts.
5. Inserts all entries except the root (`new_files_data[1:]`) via `file_service.insert_file`.
6. Calls [`update_files_parent`](#update_files_parent-sync) to set `parent` FK on every record.
7. Builds `file_paths` (local disk paths) and `file_urls` (S3 keys) for the upload step.

### Returns

```python
{
    "file_paths": List[str],  # local paths including folders
    "file_urls":  List[str],  # S3 keys (empty string for folders)
}
```

### Example

```python
# file_list after prepend:
["report/", "report/folder1/", "report/folder1/file.txt"]

# Returned:
{
    "file_paths": [
        "./work_dir/f47ac10b/",
        "./work_dir/f47ac10b/folder1/",
        "./work_dir/f47ac10b/folder1/file.txt",
    ],
    "file_urls": ["", "", "uuid-1.txt"],
}
```

---

## `update_files_parent` (sync)

**Prefect task name:** `update-files-parent`

Iterates over all inserted items and sets the correct `parent` database foreign key on each file record, using the index-based parent mapping from `parents_data`.

### Inputs

| Parameter               | Type               | Description |
|-------------------------|--------------------|-------------|
| `selected_workspace_id` | `str`              | Workspace context. |
| `loggedin_user_id`      | `str`              | User context. |
| `items_data`            | `List[ItemSchema]` | All inserted items, root first. |
| `parents_data`          | `List[ParentData]` | One entry per item with its parent index. |

### Steps

For each item at index `i`:
1. Get `parent_index = parents_data[i].parent`.
2. If `parent_index` is not `None` and is within bounds: `parent_id = items_data[parent_index].id`.
3. Otherwise: `parent_id = None`.
4. Call `file_service.update_file_field_by_id(..., "parent", parent_id)`.

### Example

```
items_data   = [item(id=10), item(id=11), item(id=12)]
parents_data = [ParentData(parent=None), ParentData(parent=0), ParentData(parent=1)]

→ item id=10 → parent = None
→ item id=11 → parent = 10
→ item id=12 → parent = 11
```

---

## `upload_files_to_s3` (sync)

**Prefect task name:** `upload-to-s3`

Uploads each locally extracted file to S3 using its pre-generated UUID-based S3 key. Skips folders.

### Inputs

| Parameter    | Type        | Description |
|--------------|-------------|-------------|
| `file_paths` | `list[str]` | Local paths to all extracted entries (files and folders). |
| `file_urls`  | `list[str]` | Corresponding S3 keys (empty string `""` for folders). |

### Steps

Iterates over `file_paths` by index. For each entry:
- If `file_path` ends with `/` → skip (directory).
- Otherwise → call `S3ClientService.upload_local_file(file_path, file_urls[idx])`.

### Example

```
file_paths = ["./work_dir/f47ac10b/folder1/", "./work_dir/f47ac10b/folder1/file.txt"]
file_urls  = ["",                              "uuid-1.txt"]

→ index 0: ends with "/" → skip
→ index 1: upload ./…/file.txt → S3 key "uuid-1.txt"
```

---

## `update_upload_status` (async)

**Prefect task name:** `update-upload-status`

Marks the root output folder item as fully uploaded by setting `is_uploaded = True` in the database.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `selected_workspace_id` | `str` | Workspace context. |
| `loggedin_user_id`      | `str` | User context. |
| `output_item_id`        | `str` | DB item ID of the root folder. |

### Steps

Calls `file_service.update_file_field_by_id(..., "is_uploaded", True)` for `output_item_id`.

---

## `cleanup_temp_files` (sync)

**Prefect task name:** `cleanup-temp-files`

Deletes the temporary local working directory created during the flow.

### Inputs

| Parameter | Type  | Description |
|-----------|-------|-------------|
| `path`    | `str` | Path to the file or directory to delete. |

### Steps

- If `path` is a file → `os.remove(path)`.
- If `path` is a directory → `shutil.rmtree(path)` (recursive delete).

### Example

```
path = "./work_dir/f47ac10b"
→ shutil.rmtree("./work_dir/f47ac10b")   # entire folder removed
```
