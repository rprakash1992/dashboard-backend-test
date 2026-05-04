# Main Flow: `extract_zip_workflow`

**Prefect flow name:** `extract-zip-workflow`
**Type:** async
**Source:** `api_server/app/flows/extract_zip_flow.py`

---

## Flow Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `loggedin_user_id`      | `str` | ID of the user triggering the extraction. |
| `selected_workspace_id` | `str` | Workspace where the zip and output folder reside. |
| `input_item_id`         | `str` | DB item ID of the zip file to extract. |
| `output_item_id`        | `str` | DB item ID of the pre-created root folder for the output. |

> The root folder (`output_item_id`) **must already exist** in the database before the flow is invoked. The flow only creates its children.

---

## Execution Steps

### Step 0 — Prepare

```python
prepare_extract_response = await prepare_extraction(
    loggedin_user_id, selected_workspace_id, input_item_id
)
```

Resolves the S3 key, strips the file extension from the item title, and builds unique local paths for this run.

**Outputs used downstream:**
- `download_path` — where the zip will be saved locally
- `extraction_path` — the unique working directory for this run
- `item_title` — display name for the root folder
- `file_s3_key` — S3 object key of the zip

See: [tasks.md — prepare_extraction](tasks.md#prepare_extraction-async)

---

### Step 1 — Download

```python
await download_file_from_s3(file_s3_key, download_path)
```

Downloads the zip file from S3 to `download_path` on the local filesystem.

See: [tasks.md — download_file_from_s3](tasks.md#download_file_from_s3-async)

---

### Step 2 — Extract

```python
file_list_extracted = extract_zip_file(download_path, extraction_path)
```

Extracts all zip contents to `extraction_path` and returns the raw `namelist()` of internal paths.

See: [tasks.md — extract_zip_file](tasks.md#extract_zip_file-sync)

---

### Step 3 — Update Database

```python
update_database_response = await update_database_records(
    loggedin_user_id, selected_workspace_id, item_title,
    output_item_id, file_list_extracted, extraction_path
)
```

Inserts all folders and files from the zip into the database, sets parent-child FK relationships, and returns the local file paths and S3 keys for the upload step.

**Outputs used downstream:**
- `file_paths` — local disk paths of extracted entries
- `file_urls` — S3 keys for each entry (empty string for folders)

See: [tasks.md — update_database_records](tasks.md#update_database_records-async)

---

### Step 4 — Upload to S3

```python
upload_files_to_s3(file_paths, file_urls)
```

Uploads each extracted file (not folders) to S3 using its pre-generated UUID S3 key.

See: [tasks.md — upload_files_to_s3](tasks.md#upload_files_to_s3-sync)

---

### Step 5 — Update Upload Status

```python
await update_upload_status(selected_workspace_id, loggedin_user_id, output_item_id)
```

Marks the root folder item as `is_uploaded = True` in the database, signalling to the frontend that the extraction is complete.

See: [tasks.md — update_upload_status](tasks.md#update_upload_status-async)

---

### Step 6 — Cleanup

```python
cleanup_temp_files(extraction_path)
```

Deletes the entire `extraction_path` directory, removing the downloaded zip and all extracted files from local disk.

See: [tasks.md — cleanup_temp_files](tasks.md#cleanup_temp_files-sync)

---

## Data Flow Summary

```
prepare_extraction
    └─ file_s3_key ──────────────────────────► download_file_from_s3
    └─ download_path ────────────────────────► download_file_from_s3
    │                                           download_file_from_s3
    │                                               └─ (file on disk)
    └─ extraction_path ──────────────────────► extract_zip_file
    │                                           extract_zip_file
    │                                               └─ file_list_extracted
    └─ item_title ───────────────────────────► update_database_records ◄── file_list_extracted
    └─ extraction_path ──────────────────────► update_database_records
                                                update_database_records
                                                    └─ file_paths ───────► upload_files_to_s3
                                                    └─ file_urls ────────► upload_files_to_s3

output_item_id ──────────────────────────────► update_database_records
               ──────────────────────────────► update_upload_status
```

---

## Error Handling

| Failure point | Behaviour |
|---|---|
| `file_s3_key` is empty | `prepare_extraction` raises `ValueError` — flow aborts before any download or DB writes. |
| S3 download fails | Prefect retries according to task retry policy (if configured). |
| DB insert fails | Exception propagates and the flow fails; already-inserted records remain in DB. |
| `cleanup_temp_files` fails | The flow has already completed all meaningful work; the local directory may need manual cleanup. |
