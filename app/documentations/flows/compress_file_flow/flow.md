# Main Flow: `compress_file_workflow`

**Prefect flow name:** `compress-file-workflow`
**Type:** async
**Source:** `api_server/app/flows/compress_file_flow.py`

---

## Flow Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `selected_workspace_id` | `str` | Workspace where the input folder and output zip item reside. |
| `loggedin_user_id`      | `str` | ID of the user triggering the compression. |
| `input_item_id`         | `str` | DB item ID of the folder to compress. |
| `output_item_id`        | `str` | DB item ID of the pre-created output zip file item. |

> The output zip item (`output_item_id`) **must already exist** in the database before the flow is invoked. The flow writes the zip to that item's S3 key and marks it as uploaded.

---

## Execution Steps

### Step 1 — Prepare

```python
response = await prepare_compression(
    selected_workspace_id, loggedin_user_id, input_item_id, output_item_id
)
```

Fetches the output zip's S3 key and the input folder's title from the database. Recursively builds the full `file_paths` / `file_urls` lists by traversing the folder tree, then generates a unique local working directory for this run.

**Outputs used downstream:**

| Variable              | Description |
|-----------------------|-------------|
| `file_paths`          | Relative paths of all entries (folders + files) |
| `file_urls`           | S3 key per entry (empty for folders) |
| `file_download_path`  | Root local working directory (`./work_dir/<uuid>`) |
| `directory_to_zip`    | Subfolder inside `file_download_path` to zip |
| `compressed_zip_path` | Local path for the output `.zip` file |
| `output_file_url`     | S3 key to upload the zip to |

See: [tasks.md — prepare_compression](tasks.md#prepare_compression-async)

---

### Step 2 — Download

```python
download_s3_objects(file_paths, file_urls, file_download_path)
```

Downloads every file from S3 into `file_download_path`, recreating the exact folder hierarchy. Folder entries (empty S3 key) are skipped — directories are created automatically by `download_file_from_s3` when a file inside them is downloaded.

See: [tasks.md — download_s3_objects](tasks.md#download_s3_objects-sync)

---

### Step 3 — Zip

```python
zip_directory(directory_to_zip, compressed_zip_path)
```

Walks `directory_to_zip` recursively and writes all files into a new zip at `compressed_zip_path` using `ZIP_DEFLATED` compression, preserving relative paths inside the archive.

See: [tasks.md — zip_directory](tasks.md#zip_directory-sync)

---

### Step 4 — Upload

```python
upload_zip_to_s3(compressed_zip_path, output_file_url)
```

Verifies the zip exists locally then uploads it to S3 under `output_file_url`.

See: [tasks.md — upload_zip_to_s3](tasks.md#upload_zip_to_s3-sync)

---

### Step 5 — Update Status

```python
await update_upload_status(selected_workspace_id, loggedin_user_id, output_item_id)
```

Sets `is_uploaded = True` on the output zip item in the database, signalling to the frontend that the zip is ready.

See: [tasks.md — update_upload_status](tasks.md#update_upload_status-async)

---

### Step 6 — Cleanup

```python
cleanup_temp_files(file_download_path)
```

Deletes the entire `file_download_path` directory, removing all downloaded files and the generated zip from local disk.

See: [tasks.md — cleanup_temp_files](tasks.md#cleanup_temp_files-sync)

---

## Data Flow Summary

```
prepare_compression
    └─ file_paths ───────────────────────────► download_s3_objects
    └─ file_urls ────────────────────────────► download_s3_objects
    └─ file_download_path ───────────────────► download_s3_objects
    │                                           download_s3_objects
    │                                               └─ (files on disk under file_download_path)
    └─ directory_to_zip  ────────────────────► zip_directory
    └─ compressed_zip_path ──────────────────► zip_directory
    │                                           zip_directory
    │                                               └─ (zip file at compressed_zip_path)
    └─ compressed_zip_path ──────────────────► upload_zip_to_s3
    └─ output_file_url ──────────────────────► upload_zip_to_s3

output_item_id ──────────────────────────────► update_upload_status

file_download_path ──────────────────────────► cleanup_temp_files
```

---

## Error Handling

| Failure point | Behaviour |
|---|---|
| Input folder has no children | `file_paths[0]` in `prepare_compression` raises `IndexError` — flow aborts before any download. |
| S3 download fails | Exception propagates from `download_s3_objects`; flow fails before zipping. |
| Zip file not created | `upload_zip_to_s3` raises `FileNotFoundError` explicitly. |
| DB update fails | `update_upload_status` raises; zip is already uploaded to S3 but marked as not uploaded in DB. |
| Cleanup fails | The flow has already completed all meaningful work; the local directory may need manual cleanup. |
