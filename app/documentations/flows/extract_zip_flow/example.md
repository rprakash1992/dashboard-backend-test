# End-to-End Example

This walkthrough traces a complete execution of `extract_zip_workflow` with concrete data at every step.

---

## Scenario

A user has uploaded a zip file called `project.zip` to their workspace. The zip contains:

```
folder1/
folder1/design.vcp
folder1/notes/
folder1/notes/readme.txt
```

The user triggers an extraction. The system has already created a root folder item in the database to represent the extracted output.

---

## Flow Inputs

```python
loggedin_user_id      = "user-42"
selected_workspace_id = "ws-99"
input_item_id         = "item-001"   # DB record for project.zip
output_item_id        = "item-002"   # DB record for the pre-created root folder
```

---

## Step 0 — `prepare_extraction`

The task fetches `item-001` from the database:
- `file.url` (S3 key) = `"project.zip"`
- `item.title` = `"project.zip"` → stripped to `"project"`

A UUID is generated: `f47ac10b-58cc-4372-a567-0e02b2c3d479`

**Output:**
```python
PrepareExtractionResponse(
    file_s3_key          = "project.zip",
    file_download_path   = "./work_dir/f47ac10b-58cc-4372-a567-0e02b2c3d479/project.zip",
    file_extraction_path = "./work_dir/f47ac10b-58cc-4372-a567-0e02b2c3d479",
    item_title           = "project",
)
```

---

## Step 1 — `download_file_from_s3`

```
S3 key:        "project.zip"
Download path: "./work_dir/f47ac10b-…/project.zip"

→ Creates directory ./work_dir/f47ac10b-…/
→ Downloads project.zip from S3 to that path
```

Local filesystem after this step:
```
./work_dir/
  f47ac10b-…/
    project.zip
```

---

## Step 2 — `extract_zip_file`

```
zip_path   = "./work_dir/f47ac10b-…/project.zip"
extract_to = "./work_dir/f47ac10b-…"
```

**Returns (raw namelist from zip):**
```python
file_list_extracted = [
    "folder1/",
    "folder1/design.vcp",
    "folder1/notes/",
    "folder1/notes/readme.txt",
]
```

Local filesystem after this step:
```
./work_dir/
  f47ac10b-…/
    project.zip
    folder1/
      design.vcp
      notes/
        readme.txt
```

---

## Step 3 — `update_database_records`

### 3a. Build full file list (root prepended)

```python
file_list = [
    "project/",                        # index 0  ← prepended
    "project/folder1/",                # index 1
    "project/folder1/design.vcp",      # index 2
    "project/folder1/notes/",          # index 3
    "project/folder1/notes/readme.txt",# index 4
]
```

### 3b. Compute titles and parent indices

| Index | Zip path | Display title | parent | isFolder |
|-------|----------|---------------|--------|----------|
| 0 | `project/` | `project` | `None` | `True` |
| 1 | `project/folder1/` | `folder1` | `0` | `True` |
| 2 | `project/folder1/design.vcp` | `design.vcp` | `1` | `False` |
| 3 | `project/folder1/notes/` | `notes` | `1` | `True` |
| 4 | `project/folder1/notes/readme.txt` | `readme.txt` | `3` | `False` |

### 3c. Build file record dicts

```python
new_files_data = [
    {"title": "project",    "url": "",             "file_extension": "vcollab_folder", ...},  # index 0 — skipped (already in DB as output_item_id)
    {"title": "folder1",    "url": "",             "file_extension": "vcollab_folder", ...},  # index 1
    {"title": "design.vcp", "url": "uuid-a.vcp",   "file_extension": "vcp",            ...},  # index 2
    {"title": "notes",      "url": "",             "file_extension": "vcollab_folder", ...},  # index 3
    {"title": "readme.txt", "url": "uuid-b.txt",   "file_extension": "txt",            ...},  # index 4
]
```

### 3d. DB inserts (indices 1–4)

```
file_service.insert_file(...) × 4
→ Returns new DB item IDs: item-003, item-004, item-005, item-006
```

### 3e. `update_files_parent`

```
items_data = [item-002, item-003, item-004, item-005, item-006]
             (root)     (folder1) (design)  (notes)   (readme)

→ item-002.parent = None         (root)
→ item-003.parent = item-002.id  (folder1 inside root)
→ item-004.parent = item-003.id  (design.vcp inside folder1)
→ item-005.parent = item-003.id  (notes inside folder1)
→ item-006.parent = item-005.id  (readme.txt inside notes)
```

### 3f. Build file_paths and file_urls

```python
file_paths = [
    "./work_dir/f47ac10b-…/",
    "./work_dir/f47ac10b-…/folder1/",
    "./work_dir/f47ac10b-…/folder1/design.vcp",
    "./work_dir/f47ac10b-…/folder1/notes/",
    "./work_dir/f47ac10b-…/folder1/notes/readme.txt",
]

file_urls = ["", "", "uuid-a.vcp", "", "uuid-b.txt"]
```

---

## Step 4 — `upload_files_to_s3`

| Index | `file_path` | `file_url` | Action |
|-------|-------------|------------|--------|
| 0 | `./…/` | `""` | Skip (ends with `/`) |
| 1 | `./…/folder1/` | `""` | Skip (ends with `/`) |
| 2 | `./…/folder1/design.vcp` | `"uuid-a.vcp"` | Upload → S3 key `uuid-a.vcp` |
| 3 | `./…/folder1/notes/` | `""` | Skip (ends with `/`) |
| 4 | `./…/folder1/notes/readme.txt` | `"uuid-b.txt"` | Upload → S3 key `uuid-b.txt` |

---

## Step 5 — `update_upload_status`

```
file_service.update_file_field_by_id(
    workspace_id = "ws-99",
    user_id      = "user-42",
    item_id      = "item-002",   ← root folder
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

Local filesystem after cleanup:
```
./work_dir/
  (empty)
```

---

## Final Database State

| Item ID | Title | File extension | URL | Parent |
|---------|-------|----------------|-----|--------|
| item-002 | project | vcollab_folder | `` | `None` |
| item-003 | folder1 | vcollab_folder | `` | item-002 |
| item-004 | design.vcp | vcp | uuid-a.vcp | item-003 |
| item-005 | notes | vcollab_folder | `` | item-003 |
| item-006 | readme.txt | txt | uuid-b.txt | item-005 |

This structure mirrors the original zip layout and is traversable in the frontend file browser via the parent foreign keys.
