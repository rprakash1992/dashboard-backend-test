# Prefect Tasks

Each function below is decorated with `@task` and runs as a tracked step in the `extract-zip-workflow-with-folder-structure` Prefect flow.

---

## `prepare_extraction` (async)

**Prefect task name:** `prepare-extraction`

Fetches the zip file's S3 key and item title from the database, generates a unique local working directory, and assembles all path information needed by downstream tasks.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `loggedin_user_id`      | `str` | ID of the requesting user. |
| `selected_workspace_id` | `str` | Workspace context. |
| `input_item_id`         | `str` | DB item ID of the zip file to extract. |

### Steps

1. Opens DB sessions (`get_dashboard_db`, `get_prefect_db`).
2. Fetches the `FileSchema` for `input_item_id` → gets `file.url` as the S3 key.
3. Generates a UUID for a unique local working directory.
4. Fetches the `ItemSchema` for `input_item_id` → gets the display title.
5. Strips the file extension from the title (e.g. `"my_workflow.zip"` → `"my_workflow"`).
6. Returns a [`PrepareExtractionResponse`](data_models.md#prepareextractionresponse).

### Raises

`ValueError` if `file_s3_key` is empty or falsy.

### Returns

[`PrepareExtractionResponse`](data_models.md#prepareextractionresponse)

### Example

```python
# input_item_id = "item-001" → file.url = "my_workflow.zip", item.title = "my_workflow.zip"

PrepareExtractionResponse(
    file_s3_key          = "my_workflow.zip",
    file_download_path   = "./work_dir/f47ac10b/my_workflow.zip",
    file_extraction_path = "./work_dir/f47ac10b",
    item_title           = "my_workflow",
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

1. Creates all parent directories via `os.makedirs(..., exist_ok=True)`.
2. Calls `S3ClientService.download_file_to_local_path(file_s3_key, download_path)`.

### Example

```
file_s3_key   = "my_workflow.zip"
download_path = "./work_dir/f47ac10b/my_workflow.zip"

→ Creates ./work_dir/f47ac10b/
→ Downloads S3:"my_workflow.zip" to ./work_dir/f47ac10b/my_workflow.zip
```

---

## `extract_zip_file` (sync)

**Prefect task name:** `extract-zip-file`

Extracts all contents of the downloaded zip file and returns the internal path list.

### Inputs

| Parameter    | Type  | Description |
|--------------|-------|-------------|
| `zip_path`   | `str` | Local path to the `.zip` file. |
| `extract_to` | `str` | Local directory to extract files into. |

### Returns

`list[str]` — the zip's `namelist()` (relative paths of all entries; folders end with `/`).

### Example

```
zip_path   = "./work_dir/f47ac10b/my_workflow.zip"
extract_to = "./work_dir/f47ac10b"

→ Returns:
["workflow.py", "requirements.txt", "utils/", "utils/helper.py"]
```

---

## `build_file_paths_and_urls` (async)

**Prefect task name:** `update-database` *(note: name is outdated — no DB writes occur)*

Builds two parallel lists: local disk paths for the extracted files and S3 destination keys constructed from the workflow record's `s3_key` prefix. Does **not** insert anything into the database.

### Inputs

| Parameter               | Type        | Description |
|-------------------------|-------------|-------------|
| `loggedin_user_id`      | `str`       | User context. |
| `selected_workspace_id` | `str`       | Workspace context. |
| `item_title`            | `str`       | Root folder name (zip title without extension). |
| `output_item_id`        | `Any`       | DB ID of the workflow record. Used to fetch `workflow.s3_key`. |
| `file_list_extracted`   | `list[str]` | Raw zip namelist from `extract_zip_file`. |
| `extraction_path`       | `str`       | Local directory where files were extracted. |

### Steps

1. Opens a DB session.
2. Prepends `"<item_title>/"` to `file_list_extracted` to form the full `file_list`.
3. Fetches the workflow record for `output_item_id` → gets `workflow.s3_key`.
4. Builds `file_urls`: folders get `""`, files get `"<s3_key>/<relative_path_inside_zip>"`.
5. Builds `file_paths`: local disk paths derived from `extraction_path`.
6. Returns both lists.

### S3 key construction

For a file entry like `"my_workflow/workflow.py"`:
```python
s3_key_of_flow = "workflows/my_workflow"
relative_path  = file_list_item[file_list_item.find('/') + 1:]  # → "workflow.py"
url            = f"{s3_key_of_flow}/{relative_path}"             # → "workflows/my_workflow/workflow.py"
```

For a folder entry ending with `/`: `url = ""`

### Returns

```python
{
    "file_paths": List[str],  # local disk paths
    "file_urls":  List[str],  # S3 destination keys (empty for folders)
}
```

### Example

```python
# workflow.s3_key = "workflows/my_workflow"
# item_title = "my_workflow"
# file_list_extracted = ["workflow.py", "requirements.txt", "utils/", "utils/helper.py"]

file_list = [
    "my_workflow/",
    "my_workflow/workflow.py",
    "my_workflow/requirements.txt",
    "my_workflow/utils/",
    "my_workflow/utils/helper.py",
]

# Returns:
{
    "file_paths": [
        "./work_dir/f47ac10b/",
        "./work_dir/f47ac10b/workflow.py",
        "./work_dir/f47ac10b/requirements.txt",
        "./work_dir/f47ac10b/utils/",
        "./work_dir/f47ac10b/utils/helper.py",
    ],
    "file_urls": [
        "",
        "workflows/my_workflow/workflow.py",
        "workflows/my_workflow/requirements.txt",
        "",
        "workflows/my_workflow/utils/helper.py",
    ],
}
```

---

## `check_workflow_validity` (async)

**Prefect task name:** `check-workflow-validity`

Validates that the extracted zip contains a `workflow.py` file by checking the local `file_paths` list. If not found, marks the workflow record as `inactive`/`is_valid=False` and raises a `ValueError` to abort the flow.

### Inputs

| Parameter               | Type        | Description |
|-------------------------|-------------|-------------|
| `selected_workspace_id` | `str`       | Workspace context. |
| `loggedin_user_id`      | `str`       | User context. |
| `output_item_id`        | `str`       | DB ID of the workflow record to mark invalid if check fails. |
| `file_paths`            | `List[str]` | Local disk paths from `build_file_paths_and_urls`. |

### Steps

1. Takes `file_paths[0]` (the root folder path) and extracts the UUID folder name from it.
2. Constructs `workflow_file_path = f"./work_dir/{uuid_folder}/workflow.py"`.
3. Checks if `workflow_file_path` is in `file_paths`.
4. If **not found**:
   - Opens a DB session, fetches the workflow record.
   - Updates it with `status="inactive"`, `is_valid=False`.
   - Raises `ValueError("Not a valid workflow directory.")`.
5. If **found**: returns normally and the flow continues.

### Raises

`ValueError` if `workflow.py` is not found in the extracted paths.

### Known Issue

The constructed path `"./work_dir/<uuid>/workflow.py"` checks for `workflow.py` **directly at the extraction root**, not inside a subfolder. If the zip contains `my_workflow/workflow.py`, it will not match `"./work_dir/<uuid>/workflow.py"` and will always be flagged invalid.

The correct check should be:
```python
if not any(p.endswith("workflow.py") for p in file_paths):
```

### Example

```
file_paths = [
    "./work_dir/f47ac10b/",
    "./work_dir/f47ac10b/workflow.py",
    "./work_dir/f47ac10b/requirements.txt",
]

first_file_path    = "./work_dir/f47ac10b/"
unique_folder_name = "f47ac10b"
workflow_file_path = "./work_dir/f47ac10b/workflow.py"

→ "./work_dir/f47ac10b/workflow.py" IS in file_paths → check passes
```

---

## `upload_files_to_s3` (sync)

**Prefect task name:** `upload-to-s3`

Uploads each locally extracted file to S3 using its pre-computed destination key. Skips folder entries.

### Inputs

| Parameter    | Type        | Description |
|--------------|-------------|-------------|
| `file_paths` | `list[str]` | Local paths to all extracted entries. |
| `file_urls`  | `list[str]` | Corresponding S3 keys (empty string for folders). |

### Steps

For each entry:
- If `file_path` ends with `/` → skip (directory).
- Otherwise → call `S3ClientService.upload_local_file(file_path, s3_key)`.

### Example

```
file_paths = ["./work_dir/f47ac10b/", "./work_dir/f47ac10b/workflow.py"]
file_urls  = ["",                      "workflows/my_workflow/workflow.py"]

→ index 0: ends with "/" → skip
→ index 1: upload ./…/workflow.py → S3 key "workflows/my_workflow/workflow.py"
```

---

## `update_workflow` (async)

**Prefect task name:** `update-workflow-record`

Marks the workflow record as active and valid in the database after a successful extraction and upload.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `selected_workspace_id` | `str` | Workspace context. |
| `loggedin_user_id`      | `str` | User context. |
| `output_item_id`        | `str` | DB ID of the workflow record to update. |

### Steps

1. Opens a DB session, fetches the workflow record for `output_item_id`.
2. Constructs an updated `WorkflowSchema` with `status="active"` and `is_valid=True`, preserving all other fields unchanged.
3. Calls `workflow_service.update_workflow(...)`.

### Fields preserved unchanged

`id`, `s3_key`, `flow_function_name`, `deployment_id`, `deployment_name`, `flow_id`, `parameter_schema`

---

## `cleanup_temp_files` (sync)

**Prefect task name:** `cleanup-temp-files`

Deletes the local working directory created during the flow.

### Inputs

| Parameter | Type  | Description |
|-----------|-------|-------------|
| `path`    | `str` | Path to the file or directory to delete. |

### Steps

- If `path` is a file → `os.remove(path)`.
- If `path` is a directory → `shutil.rmtree(path)`.

### Example

```
path = "./work_dir/f47ac10b"
→ shutil.rmtree("./work_dir/f47ac10b")
```
