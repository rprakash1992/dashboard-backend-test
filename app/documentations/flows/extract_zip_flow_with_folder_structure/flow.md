# Main Flow: `extract_zip_workflow_with_folder_structure`

**Prefect flow name:** `extract-zip-workflow-with-folder-structure`
**Type:** async
**Source:** `api_server/app/flows/extract_zip_flow_with_folder_structure.py`

---

## Flow Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `loggedin_user_id`      | `str` | ID of the user triggering the extraction. |
| `selected_workspace_id` | `str` | Workspace where the zip and workflow record reside. |
| `input_item_id`         | `str` | DB item ID of the zip file (workflow package) to extract. |
| `output_item_id`        | `str` | DB ID of the pre-existing workflow record in the `workflows` table. |

> The workflow record (`output_item_id`) **must already exist** in the `workflows` table before the flow is invoked. Its `s3_key` field is used as the S3 path prefix for all uploaded files.

---

## Execution Steps

### Step 1 — Prepare

```python
response = await prepare_extraction(
    loggedin_user_id, selected_workspace_id, input_item_id
)
```

Fetches the zip's S3 key and display title from the database. Generates a unique UUID working directory and assembles all local path information.

**Outputs used downstream:**

| Variable           | Description |
|--------------------|-------------|
| `download_path`    | Local path to save the zip file |
| `extraction_path`  | Local working directory (`./work_dir/<uuid>`) |
| `item_title`       | Zip title without extension |
| `file_s3_key`      | S3 key of the zip file |

See: [tasks.md — prepare_extraction](tasks.md#prepare_extraction-async)

---

### Step 2 — Download

```python
await download_file_from_s3(file_s3_key, download_path)
```

Downloads the zip from S3 to `download_path`, creating any missing directories.

See: [tasks.md — download_file_from_s3](tasks.md#download_file_from_s3-async)

---

### Step 3 — Extract

```python
file_list_extracted = extract_zip_file(download_path, extraction_path)
```

Extracts all contents of the zip into `extraction_path`. Returns the raw `namelist()`.

See: [tasks.md — extract_zip_file](tasks.md#extract_zip_file-sync)

---

### Step 4 — Build File Paths and URLs

```python
response = await build_file_paths_and_urls(
    loggedin_user_id, selected_workspace_id, item_title,
    output_item_id, file_list_extracted, extraction_path
)
```

Fetches `workflow.s3_key` from the DB, then constructs:
- `file_paths`: local disk paths for each extracted entry
- `file_urls`: S3 destination keys using `<s3_key>/<relative_path>` for files, `""` for folders

**Outputs used downstream:**

| Variable     | Description |
|--------------|-------------|
| `file_paths` | Local paths (including folder entries) |
| `file_urls`  | S3 keys (empty string for folders) |

See: [tasks.md — build_file_paths_and_urls](tasks.md#build_file_paths_and_urls-async)

---

### Step 5 — Check Workflow Validity

```python
await check_workflow_validity(
    selected_workspace_id, loggedin_user_id, output_item_id, file_paths
)
```

Verifies that a `workflow.py` file exists in the extracted contents. If it does not:
- Updates the workflow record: `status="inactive"`, `is_valid=False`
- Raises `ValueError` — **flow aborts here**, skipping upload and cleanup

See: [tasks.md — check_workflow_validity](tasks.md#check_workflow_validity-async)

---

### Step 6 — Upload to S3

```python
upload_files_to_s3(file_paths, file_urls)
```

Uploads each extracted file (not folders) to S3 under its pre-computed key.

See: [tasks.md — upload_files_to_s3](tasks.md#upload_files_to_s3-sync)

---

### Step 7 — Update Workflow Record

```python
await update_workflow(selected_workspace_id, loggedin_user_id, output_item_id)
```

Sets `status="active"` and `is_valid=True` on the workflow record, signalling the workflow package is ready to use.

See: [tasks.md — update_workflow](tasks.md#update_workflow-async)

---

### Step 8 — Cleanup

```python
cleanup_temp_files(extraction_path)
```

Deletes the entire `extraction_path` directory.

See: [tasks.md — cleanup_temp_files](tasks.md#cleanup_temp_files-sync)

---

## Data Flow Summary

```
prepare_extraction
    └─ file_s3_key ──────────────────────────► download_file_from_s3
    └─ download_path ────────────────────────► download_file_from_s3
    └─ extraction_path ──────────────────────► extract_zip_file
    │                                           extract_zip_file
    │                                               └─ file_list_extracted
    └─ item_title ───────────────────────────► build_file_paths_and_urls ◄── file_list_extracted
    └─ extraction_path ──────────────────────► build_file_paths_and_urls
                                                build_file_paths_and_urls
                                                    └─ file_paths ──────────► check_workflow_validity
                                                    └─ file_paths ──────────► upload_files_to_s3
                                                    └─ file_urls ───────────► upload_files_to_s3

output_item_id ──────────────────────────────► build_file_paths_and_urls
               ──────────────────────────────► check_workflow_validity
               ──────────────────────────────► update_workflow
```

---

## Error Handling

| Failure point | Behaviour |
|---|---|
| `file_s3_key` is empty | `prepare_extraction` raises `ValueError` — flow aborts before any download. |
| S3 download fails | Exception propagates from `download_file_from_s3`; flow fails. |
| `workflow.py` not found | `check_workflow_validity` marks workflow `inactive`/`is_valid=False`, raises `ValueError` — **upload and `update_workflow` are skipped**. Cleanup is also skipped, leaving extracted files on disk. |
| Upload fails | Exception propagates; `update_workflow` is not called — workflow remains in its previous state. |
| Cleanup fails | Flow already completed meaningful work; local directory may need manual removal. |

---

## Important Notes

- `update_upload_status` (sets `is_uploaded=True` on the file record) is **commented out** in this flow. The file record's upload status is not updated.
- The `@task` name on `build_file_paths_and_urls` is still `"update-database"` in the Prefect task decorator, even though the function no longer writes to the database. This affects the label shown in the Prefect UI.
- If `check_workflow_validity` raises, `cleanup_temp_files` is never called — the `extraction_path` directory will remain on disk until manually removed.
