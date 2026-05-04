# End-to-End Example

This walkthrough traces a complete execution of `extract_zip_workflow_with_folder_structure` with concrete data at every step.

---

## Scenario

A user has uploaded a workflow package zip `my_workflow.zip` to the workspace. The zip contains:

```
workflow.py
requirements.txt
utils/
utils/helper.py
```

The system has pre-created a workflow record in the `workflows` table with a fixed S3 key prefix. The user triggers the extraction to deploy the workflow.

---

## Database State Before the Flow

**Files table:**

| Item ID  | url (S3 key)       |
|----------|--------------------|
| item-001 | `my_workflow.zip`  |

**Items table:**

| Item ID  | title              |
|----------|--------------------|
| item-001 | `my_workflow.zip`  |

**Workflows table:**

| ID       | s3_key                    | status     | is_valid |
|----------|---------------------------|------------|----------|
| wf-001   | `workflows/my_workflow`   | `pending`  | `False`  |

---

## Flow Inputs

```python
loggedin_user_id      = "user-42"
selected_workspace_id = "ws-99"
input_item_id         = "item-001"   # DB item for my_workflow.zip
output_item_id        = "wf-001"     # DB workflow record
```

---

## Step 1 — `prepare_extraction`

Fetches `item-001`:
- `file.url` = `"my_workflow.zip"` → `file_s3_key = "my_workflow.zip"`
- `item.title` = `"my_workflow.zip"` → strip extension → `item_title = "my_workflow"`

UUID generated: `f47ac10b-58cc-4372-a567-0e02b2c3d479`

**Output:**
```python
PrepareExtractionResponse(
    file_s3_key          = "my_workflow.zip",
    file_download_path   = "./work_dir/f47ac10b-…/my_workflow.zip",
    file_extraction_path = "./work_dir/f47ac10b-…",
    item_title           = "my_workflow",
)
```

---

## Step 2 — `download_file_from_s3`

```
S3 key:        "my_workflow.zip"
Download path: "./work_dir/f47ac10b-…/my_workflow.zip"

→ Creates directory ./work_dir/f47ac10b-…/
→ Downloads S3:"my_workflow.zip" to that path
```

**Local filesystem:**
```
./work_dir/f47ac10b-…/
  my_workflow.zip
```

---

## Step 3 — `extract_zip_file`

```
zip_path   = "./work_dir/f47ac10b-…/my_workflow.zip"
extract_to = "./work_dir/f47ac10b-…"
```

**Returns:**
```python
file_list_extracted = ["workflow.py", "requirements.txt", "utils/", "utils/helper.py"]
```

**Local filesystem after extraction:**
```
./work_dir/f47ac10b-…/
  my_workflow.zip
  workflow.py
  requirements.txt
  utils/
    helper.py
```

---

## Step 4 — `build_file_paths_and_urls`

### 4a. Construct full file_list (root prepended)

```python
file_list = [
    "my_workflow/",              # index 0 ← prepended root
    "my_workflow/workflow.py",   # index 1
    "my_workflow/requirements.txt",  # index 2
    "my_workflow/utils/",        # index 3
    "my_workflow/utils/helper.py",   # index 4
]
```

### 4b. Fetch workflow.s3_key

```
workflow record wf-001 → s3_key = "workflows/my_workflow"
```

### 4c. Build file_urls (S3 destination keys)

| Index | file_list entry | relative path (after first `/`) | file_url |
|-------|-----------------|----------------------------------|----------|
| 0 | `my_workflow/` | folder → `""` | `""` |
| 1 | `my_workflow/workflow.py` | `workflow.py` | `workflows/my_workflow/workflow.py` |
| 2 | `my_workflow/requirements.txt` | `requirements.txt` | `workflows/my_workflow/requirements.txt` |
| 3 | `my_workflow/utils/` | folder → `""` | `""` |
| 4 | `my_workflow/utils/helper.py` | `utils/helper.py` | `workflows/my_workflow/utils/helper.py` |

### 4d. Build file_paths (local disk paths)

```python
file_paths = [
    "./work_dir/f47ac10b-…/",
    "./work_dir/f47ac10b-…/workflow.py",
    "./work_dir/f47ac10b-…/requirements.txt",
    "./work_dir/f47ac10b-…/utils/",
    "./work_dir/f47ac10b-…/utils/helper.py",
]
```

---

## Step 5 — `check_workflow_validity`

```python
first_file_path    = "./work_dir/f47ac10b-…/"
unique_folder_name = "f47ac10b-…"           ← split("/")[-2]
workflow_file_path = "./work_dir/f47ac10b-…/workflow.py"
```

Check: `"./work_dir/f47ac10b-…/workflow.py"` **is in** `file_paths` → **passes**.

Flow continues to upload.

> **Failure case:** If the zip did NOT contain `workflow.py`, this check would fail:
> - Workflow record updated: `status="inactive"`, `is_valid=False`
> - `ValueError` raised → flow aborts, upload and update_workflow are skipped

---

## Step 6 — `upload_files_to_s3`

| Index | file_path | file_url | Action |
|-------|-----------|----------|--------|
| 0 | `./…/` | `""` | skip (folder) |
| 1 | `./…/workflow.py` | `workflows/my_workflow/workflow.py` | upload |
| 2 | `./…/requirements.txt` | `workflows/my_workflow/requirements.txt` | upload |
| 3 | `./…/utils/` | `""` | skip (folder) |
| 4 | `./…/utils/helper.py` | `workflows/my_workflow/utils/helper.py` | upload |

**S3 after this step:**
```
workflows/my_workflow/
  workflow.py
  requirements.txt
  utils/
    helper.py
```

---

## Step 7 — `update_workflow`

Fetches `wf-001`, constructs updated record:

```python
WorkflowSchema(
    id                 = wf-001,
    s3_key             = "workflows/my_workflow",   ← unchanged
    flow_function_name = ...,                        ← unchanged
    deployment_id      = ...,                        ← unchanged
    deployment_name    = ...,                        ← unchanged
    flow_id            = ...,                        ← unchanged
    status             = "active",                   ← updated
    is_valid           = True,                       ← updated
    parameter_schema   = ...,                        ← unchanged
)
```

---

## Step 8 — `cleanup_temp_files`

```
path = "./work_dir/f47ac10b-…"
→ shutil.rmtree("./work_dir/f47ac10b-…")
```

**Local filesystem after cleanup:**
```
./work_dir/
  (empty)
```

---

## Final State

**S3:**
```
workflows/my_workflow/workflow.py
workflows/my_workflow/requirements.txt
workflows/my_workflow/utils/helper.py
```

**Workflows table:**

| ID     | s3_key                  | status   | is_valid |
|--------|-------------------------|----------|----------|
| wf-001 | `workflows/my_workflow` | `active` | `True`   |

The workflow package is deployed and ready. The Prefect system can now reference `wf-001` to locate and run the workflow using the files at `workflows/my_workflow/` in S3.

---

## Failure Scenario: Missing `workflow.py`

If the uploaded zip does not contain `workflow.py`:

**Step 5 fails:**
```
workflow_file_path = "./work_dir/f47ac10b-…/workflow.py"
→ NOT in file_paths
→ workflow updated: status="inactive", is_valid=False
→ ValueError raised
```

**Steps 6, 7, 8 are skipped.**

**Final state on failure:**

| ID     | s3_key                  | status     | is_valid |
|--------|-------------------------|------------|----------|
| wf-001 | `workflows/my_workflow` | `inactive` | `False`  |

The local directory `./work_dir/f47ac10b-…/` remains on disk (cleanup was not reached).
