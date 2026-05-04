# End-to-End Example

This walkthrough traces a complete execution of `compress_file_workflow` with concrete data at every step.

---

## Scenario

A user has a folder called `project` in their workspace with the following structure:

```
project/
  folder1/
    design.vcp
    notes/
      readme.txt
```

Each item exists as a database record. The user triggers compression. The system has already created an output zip item in the database to hold the result.

---

## Database State Before the Flow

| Item ID  | Title       | mime_type       | url             | parent   |
|----------|-------------|-----------------|-----------------|----------|
| item-001 | project     | vcollab_folder  | `` (empty)      | `None`   |
| item-003 | folder1     | vcollab_folder  | `` (empty)      | item-001 |
| item-004 | design.vcp  | vcp             | `uuid-a.vcp`    | item-003 |
| item-005 | notes       | vcollab_folder  | `` (empty)      | item-003 |
| item-006 | readme.txt  | txt             | `uuid-b.txt`    | item-005 |
| item-002 | project.zip | zip             | `uuid-out.zip`  | `None`   |

---

## Flow Inputs

```python
selected_workspace_id = "ws-99"
loggedin_user_id      = "user-42"
input_item_id         = "item-001"   # the "project" folder
output_item_id        = "item-002"   # the pre-created "project.zip" item
```

---

## Step 1 — `prepare_compression`

### 1a. Fetch output file URL

```
output_file (item-002) → url = "uuid-out.zip"
```

### 1b. Fetch input item title

```
input_item (item-001) → title = "project"
```

### 1c. `get_file_paths_and_urls` — recursive DB traversal

Starting from `item-001` with prefix `"project/"`:

**Traversal order (depth-first):**

```
item-001 (project/)
  ├── item-003 (folder1/) → prefix: "project/"
  │     ├── item-004 (design.vcp) → prefix: "project/folder1/"
  │     └── item-005 (notes/)    → prefix: "project/folder1/"
  │           └── item-006 (readme.txt) → prefix: "project/folder1/notes/"
```

**Path building per entry:**

| Child item | title | mime_type | path_suffix | title ends with `.vcp`/`.txt`? | path |
|---|---|---|---|---|---|
| item-003 | `folder1` | `vcollab_folder` | `"/"` | n/a | `"project/folder1/"` |
| item-004 | `design.vcp` | `vcp` | `"vcp"` | yes | `"project/folder1/design.vcp"` |
| item-005 | `notes` | `vcollab_folder` | `"/"` | n/a | `"project/folder1/notes/"` |
| item-006 | `readme.txt` | `txt` | `"txt"` | yes | `"project/folder1/notes/readme.txt"` |

**Result:**
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

### 1d. Generate UUID and build local paths

```
UUID generated: f47ac10b-58cc-4372-a567-0e02b2c3d479

file_download_path  = "./work_dir/f47ac10b-58cc-4372-a567-0e02b2c3d479"
directory_to_zip    = "./work_dir/f47ac10b-…/project"       ← from file_paths[0] = "project/"
compressed_zip_path = "./work_dir/f47ac10b-…/f47ac10b-….zip"
output_file_url     = "uuid-out.zip"
```

---

## Step 2 — `download_s3_objects`

```
file_paths         = ["project/", "project/folder1/", "project/folder1/design.vcp",
                       "project/folder1/notes/", "project/folder1/notes/readme.txt"]
file_urls          = ["", "", "uuid-a.vcp", "", "uuid-b.txt"]
file_download_path = "./work_dir/f47ac10b-…"
```

| Index | file_path | file_url | Action |
|-------|-----------|----------|--------|
| 0 | `project/` | `""` | skip |
| 1 | `project/folder1/` | `""` | skip |
| 2 | `project/folder1/design.vcp` | `uuid-a.vcp` | download → `./work_dir/f47ac10b-…/project/folder1/design.vcp` |
| 3 | `project/folder1/notes/` | `""` | skip |
| 4 | `project/folder1/notes/readme.txt` | `uuid-b.txt` | download → `./work_dir/f47ac10b-…/project/folder1/notes/readme.txt` |

**Local filesystem after Step 2:**
```
./work_dir/f47ac10b-…/
  project/
    folder1/
      design.vcp          ← downloaded from S3 key "uuid-a.vcp"
      notes/
        readme.txt        ← downloaded from S3 key "uuid-b.txt"
```

---

## Step 3 — `zip_directory`

```
source_dir = "./work_dir/f47ac10b-…/project"  (absolute path resolved internally)
output_zip = "./work_dir/f47ac10b-…/f47ac10b-….zip"
```

`os.walk` traversal:

| full_path | arcname (relative to source_dir) |
|---|---|
| `.../project/folder1/design.vcp` | `folder1/design.vcp` |
| `.../project/folder1/notes/readme.txt` | `folder1/notes/readme.txt` |

**Zip contents:**
```
f47ac10b-….zip
  folder1/
    design.vcp
    notes/
      readme.txt
```

**Local filesystem after Step 3:**
```
./work_dir/f47ac10b-…/
  project/
    folder1/
      design.vcp
      notes/
        readme.txt
  f47ac10b-….zip          ← newly created
```

---

## Step 4 — `upload_zip_to_s3`

```
zip_path = "./work_dir/f47ac10b-…/f47ac10b-….zip"
s3_key   = "uuid-out.zip"

→ os.path.exists check: passes
→ S3ClientService.upload_local_file(zip_path, "uuid-out.zip")
→ Zip is now available at S3 key "uuid-out.zip"
```

---

## Step 5 — `update_upload_status`

```
file_service.update_file_field_by_id(
    workspace_id = "ws-99",
    user_id      = "user-42",
    item_id      = "item-002",
    field        = "is_uploaded",
    value        = True,
)
```

---

## Step 6 — `cleanup_temp_files`

```
path = "./work_dir/f47ac10b-…"
→ shutil.rmtree("./work_dir/f47ac10b-…")
```

**Local filesystem after Step 6:**
```
./work_dir/
  (empty)
```

---

## Final State

**S3:** `uuid-out.zip` contains the compressed `project` folder.

**Database:**

| Item ID  | Title       | is_uploaded |
|----------|-------------|-------------|
| item-002 | project.zip | `True`      |

The zip is available for download from S3. The frontend can resolve the download URL from `item-002.url = "uuid-out.zip"`.
