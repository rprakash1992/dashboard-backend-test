# Prefect Tasks

Each function below is decorated with `@task` and runs as a tracked step inside the `compress-file-workflow` Prefect flow.

---

## `prepare_compression` (async)

**Prefect task name:** `prepare-file-compression`

Fetches the output file's S3 key and the input folder's title from the database, builds the recursive file/URL lists by calling `get_file_paths_and_urls`, and computes all local paths for the run.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `selected_workspace_id` | `str` | Workspace context. |
| `loggedin_user_id`      | `str` | ID of the requesting user. |
| `input_item_id`         | `str` | DB item ID of the folder to compress. |
| `output_item_id`        | `str` | DB item ID of the pre-created output zip file item. |

### Steps

1. Opens a DB session.
2. Fetches `output_file` for `output_item_id` → gets `output_file_url` (the S3 key to upload the zip to).
3. Fetches `input_item` for `input_item_id` → gets `input_item_title` (used as the root folder name inside the zip).
4. Calls [`get_file_paths_and_urls`](helper_functions.md#get_file_paths_and_urlsloggedin_user_id-selected_workspace_id-item_id-item_title) to recursively build `file_paths` and `file_urls`.
5. Generates a UUID and builds local paths:
   - `file_download_path` = `./work_dir/<uuid>`
   - `directory_to_zip` = `./work_dir/<uuid>/<root_folder_name>`  (derived from `file_paths[0]`)
   - `compressed_zip_path` = `./work_dir/<uuid>/<uuid>.zip`
6. Returns a [`PrepareCompressionResponse`](data_models.md#preparecompressionresponse).

### Returns

[`PrepareCompressionResponse`](data_models.md#preparecompressionresponse)

### Example

```python
# Input item: folder named "project" (input_item_id="item-001")
# Output item: zip file with url="uuid-output.zip" (output_item_id="item-002")

# Returns:
PrepareCompressionResponse(
    file_paths         = ["project/", "project/folder1/", "project/folder1/design.vcp"],
    file_urls          = ["",         "",                 "uuid-a.vcp"],
    file_download_path = "./work_dir/f47ac10b",
    directory_to_zip   = "./work_dir/f47ac10b/project",
    compressed_zip_path= "./work_dir/f47ac10b/f47ac10b.zip",
    output_file_url    = "uuid-output.zip",
)
```

> **Note:** If `file_paths` is empty (the input folder has no children), accessing `file_paths[0]` at the `directory_to_zip` derivation step will raise an `IndexError`.

---

## `download_s3_objects` (sync)

**Prefect task name:** `download-s3-objects`

Iterates over the `file_paths` / `file_urls` lists and downloads every file from S3, recreating the original folder hierarchy under `file_download_path`.

### Inputs

| Parameter            | Type        | Description |
|----------------------|-------------|-------------|
| `file_paths`         | `List[str]` | Relative paths for all entries. Folders end with `/`. |
| `file_urls`          | `List[str]` | S3 key per entry. Empty string for folders. |
| `file_download_path` | `str`       | Root local directory to download into. |

### Steps

For each index `idx` in `file_paths`:
1. Get `s3_key = file_urls[idx]`.
2. If `s3_key` is empty (folder) → skip.
3. Otherwise → build `download_path = f"{file_download_path}/{file_paths[idx]}"` and call [`download_file_from_s3`](helper_functions.md#download_file_from_s3file_s3_key-download_path).

### Example

```
file_paths         = ["project/", "project/folder1/", "project/folder1/design.vcp"]
file_urls          = ["",         "",                 "uuid-a.vcp"]
file_download_path = "./work_dir/f47ac10b"

→ index 0: s3_key="" → skip
→ index 1: s3_key="" → skip
→ index 2: download S3:"uuid-a.vcp" → "./work_dir/f47ac10b/project/folder1/design.vcp"
```

Local filesystem after this task:
```
./work_dir/f47ac10b/
  project/
    folder1/
      design.vcp
```

---

## `zip_directory` (sync)

**Prefect task name:** `zip-directory`

Walks `source_dir` recursively and writes all files into a new zip archive at `output_zip`, preserving the internal relative path structure.

### Inputs

| Parameter    | Type  | Description |
|--------------|-------|-------------|
| `source_dir` | `str` | Local directory to zip. Converted to absolute path internally. |
| `output_zip` | `str` | Local path for the output `.zip` file. Converted to absolute path internally. |

### Steps

1. Converts both paths to absolute with `os.path.abspath`.
2. Opens `output_zip` as a `ZipFile` with `ZIP_DEFLATED` compression.
3. Walks `source_dir` with `os.walk`. For each file:
   - Computes `arcname = os.path.relpath(full_path, source_dir)` — the path inside the zip relative to `source_dir`.
   - Writes the file to the zip under `arcname`.

### Example

```
source_dir = "./work_dir/f47ac10b/project"
output_zip = "./work_dir/f47ac10b/f47ac10b.zip"

Directory contents:
  ./work_dir/f47ac10b/project/
    folder1/
      design.vcp
      notes/
        readme.txt

Zip contents:
  folder1/design.vcp
  folder1/notes/readme.txt
```

> **Known limitation:** `os.walk` only iterates over files. **Empty subdirectories are silently omitted** from the zip. If the folder tree contains empty folders, they will not appear in the resulting zip file.

---

## `upload_zip_to_s3` (sync)

**Prefect task name:** `upload-zip-to-s3`

Uploads the locally created zip file to S3 under the output item's pre-assigned S3 key.

### Inputs

| Parameter  | Type  | Description |
|------------|-------|-------------|
| `zip_path` | `str` | Local path to the `.zip` file. |
| `s3_key`   | `str` | S3 object key to upload to. |

### Steps

1. Checks `os.path.exists(zip_path)` — raises `FileNotFoundError` if the zip was not created.
2. Calls `S3ClientService.upload_local_file(zip_path, s3_key)`.

### Example

```
zip_path = "./work_dir/f47ac10b/f47ac10b.zip"
s3_key   = "uuid-output.zip"

→ Uploads the zip to S3 under key "uuid-output.zip"
```

---

## `update_upload_status` (async)

**Prefect task name:** `update-upload-status`

Marks the output zip item as fully uploaded in the database by setting `is_uploaded = True`.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `selected_workspace_id` | `str` | Workspace context. |
| `loggedin_user_id`      | `str` | User context. |
| `output_item_id`        | `str` | DB item ID of the output zip file. |

### Steps

Opens a DB session and calls `file_service.update_file_field_by_id(..., "is_uploaded", True)` for `output_item_id`.

---

## `cleanup_temp_files` (sync)

**Prefect task name:** `cleanup-temp-files`

Deletes the temporary local working directory created during the flow, including all downloaded files and the generated zip.

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
→ shutil.rmtree("./work_dir/f47ac10b")
  removes: project/, project/folder1/, project/folder1/design.vcp, f47ac10b.zip
```
