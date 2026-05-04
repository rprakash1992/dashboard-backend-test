# Extract Zip Workflow With Folder Structure

## Purpose

This workflow is a **workflow-package variant** of the standard zip extraction flow. It is used specifically to upload a Prefect workflow package (a zip file containing `workflow.py` and supporting files) to S3 and register it in the `workflows` table.

Unlike `extract_zip_flow.py` which creates items/files records in the dashboard database, this flow:
- Extracts the zip and uploads its contents to S3 under a structured path derived from the workflow's pre-assigned `s3_key`
- Validates that the zip contains a `workflow.py` file
- Updates the workflow record's `status` and `is_valid` fields on success or failure

---

## Source File

`api_server/app/flows/extract_zip_flow_with_folder_structure.py`

---

## Documentation Index

| File | Contents |
|------|----------|
| [data_models.md](data_models.md) | Pydantic models used across the flow |
| [tasks.md](tasks.md) | All Prefect tasks with inputs, logic, and examples |
| [flow.md](flow.md) | Main Prefect flow and execution order |
| [example.md](example.md) | Full end-to-end walkthrough with concrete data |

---

## High-Level Diagram

```
[Inputs: input_item_id (zip file), output_item_id (pre-existing workflow DB record)]
         |
         v
  prepare_extraction              →  resolves S3 key, item title, local paths
         |
         v
  download_file_from_s3           →  downloads zip from S3 to ./work_dir/<uuid>/
         |
         v
  extract_zip_file                →  extracts zip locally, returns namelist
         |
         v
  build_file_paths_and_urls       →  builds local file_paths and S3 file_urls
         |                            using workflow.s3_key as path prefix
         v
  check_workflow_validity         →  verifies workflow.py exists in file_paths
         |                            marks workflow inactive+invalid if not found
         v
  upload_files_to_s3              →  uploads each extracted file to S3
         |
         v
  update_workflow                 →  sets workflow status="active", is_valid=True
         |
         v
  cleanup_temp_files              →  deletes ./work_dir/<uuid>/
```

---

## Key Differences from `extract_zip_flow.py`

| Aspect | `extract_zip_flow.py` | This flow |
|---|---|---|
| DB writes | Inserts items + files into dashboard DB | No item/file inserts — only updates the `workflows` table |
| S3 key generation | UUID per file | Uses `workflow.s3_key` as a fixed prefix for all files |
| Validation | None | Checks for presence of `workflow.py` |
| Final status update | Sets `is_uploaded=True` on file | Sets `status="active"`, `is_valid=True` on workflow record |
| Use case | General zip extraction | Workflow package deployment |

---

## Key Concepts

**`input_item_id`** — DB item ID of the zip file containing the workflow package.

**`output_item_id`** — DB ID of a record in the `workflows` table that must already exist. Its `s3_key` field defines the S3 path prefix under which all extracted files will be stored.

**`workflow.s3_key`** — A pre-assigned path prefix in S3 (e.g. `"workflows/my_workflow"`). All files extracted from the zip are uploaded under this prefix: `<s3_key>/<relative_path_inside_zip>`.

**Validity check** — The flow checks whether any file path in the extracted contents ends with `workflow.py`. If not, the workflow record is marked `status="inactive"`, `is_valid=False` and the flow raises a `ValueError`.
