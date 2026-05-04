# Helper Functions

These are plain functions (no Prefect `@task` decoration). They are called by Prefect tasks internally and are not tracked as individual steps in the Prefect UI.

---

## `download_file_from_s3(file_s3_key, download_path)`

Downloads a single file from S3 to a local path, creating any missing parent directories automatically.

### Inputs

| Parameter       | Type  | Description |
|-----------------|-------|-------------|
| `file_s3_key`   | `str` | S3 object key of the file to download. |
| `download_path` | `str` | Full absolute or relative local path where the file should be saved. |

### Steps

1. Calls `os.makedirs(os.path.dirname(download_path), exist_ok=True)` to ensure the directory exists.
2. Calls `S3ClientService.download_file_to_local_path(file_s3_key, download_path)`.

### Example

```
file_s3_key   = "uuid-a.vcp"
download_path = "./work_dir/f47ac10b/project/folder1/design.vcp"

→ Creates ./work_dir/f47ac10b/project/folder1/ if it doesn't exist
→ Downloads S3:"uuid-a.vcp" to that path
```

> Called by `download_s3_objects` for every non-folder entry in the path list.

---

## `get_file_paths_and_urls(loggedin_user_id, selected_workspace_id, item_id, item_title)`

Recursively traverses the database parent-child tree starting from `item_id` and builds two parallel lists: relative file paths (mirroring the folder structure) and their corresponding S3 keys.

This function opens its own DB session internally and uses an inner recursive async helper `_get_files_by_field_name_field_val`.

### Inputs

| Parameter               | Type  | Description |
|-------------------------|-------|-------------|
| `loggedin_user_id`      | `str` | User context. |
| `selected_workspace_id` | `str` | Workspace context. |
| `item_id`               | `str` | DB item ID of the root folder to traverse. |
| `item_title`            | (untyped) | Display title of the root folder — used as the base path prefix. |

### Returns

[`FilePathsAndUrlsResponse`](data_models.md#filepathsandurlsresponse)

### How it works

1. Initialises `paths = ["<item_title>/"]` and `file_urls = [""]` (the root folder entry).
2. Calls `_get_files_by_field_name_field_val` starting from `item_id` with prefix `"<item_title>/"`.
3. The inner function queries all children with `parent == item_id` from the files table.
4. For each child:
   - Fetches its item record to get the `title`.
   - Determines `path_suffix`:
     - `"/"` if `mime_type == "vcollab_folder"` (it's a subfolder)
     - `mime_type` (the file extension) otherwise
   - Builds the relative path:
     - If the title already ends with `.{mime_type}` → use `title` as-is
     - Otherwise → append `.{mime_type}` to `title`
   - Appends `path` and `file_url` to the lists.
   - Recurses into the child using the current `path` as the new prefix.

### Path building rules

| Child type | `path_suffix` | Example title | Resulting path |
|---|---|---|---|
| Subfolder | `"/"` | `notes` | `project/folder1/notes/` |
| File (title has extension) | `"vcp"` | `design.vcp` | `project/folder1/design.vcp` |
| File (title has no extension) | `"vcp"` | `design` | `project/folder1/design.vcp` |

### Example

**Database structure:**
```
project (id=item-001)
  └── folder1 (id=item-003, mime_type=vcollab_folder)
        ├── design.vcp (id=item-004, mime_type=vcp, url=uuid-a.vcp)
        └── notes (id=item-005, mime_type=vcollab_folder)
              └── readme.txt (id=item-006, mime_type=txt, url=uuid-b.txt)
```

**Output:**
```python
FilePathsAndUrlsResponse(
    file_paths = [
        "project/",
        "project/folder1/",
        "project/folder1/design.vcp",
        "project/folder1/notes/",
        "project/folder1/notes/readme.txt",
    ],
    file_urls = ["", "", "uuid-a.vcp", "", "uuid-b.txt"],
)
```

> **Known issue:** `fetch_items_by_ids` is called once per child inside the loop (N+1 queries). For large folder trees this generates many individual DB round-trips. A future optimisation would batch all child IDs into a single `fetch_items_by_ids` call per level.
