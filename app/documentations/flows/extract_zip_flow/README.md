# Extract Zip Workflow

## Purpose

This workflow extracts a zip file stored in AWS S3, mirrors its internal folder/file structure in the application database, uploads the extracted files back to S3, and cleans up temporary local files.

It is triggered when a user wants to "unzip" a zip file that has already been uploaded to a workspace. The zip's internal structure (folders and files) is reconstructed in the database and made available in the frontend file browser.

---

## Source File

`api_server/app/flows/extract_zip_flow.py`

---

## Documentation Index

| File | Contents |
|------|----------|
| [data_models.md](data_models.md) | Pydantic models used across the flow |
| [helper_functions.md](helper_functions.md) | Pure utility functions (no Prefect decoration) |
| [tasks.md](tasks.md) | Individual Prefect tasks |
| [flow.md](flow.md) | Main Prefect flow and execution order |
| [example.md](example.md) | Full end-to-end walkthrough with concrete data |

---

## High-Level Diagram

```
[Inputs: input_item_id (zip), output_item_id (pre-created root folder)]
         |
         v
  prepare_extraction          →  resolves S3 key, item title, local paths
         |
         v
  download_file_from_s3       →  downloads zip from S3 to ./work_dir/<uuid>/
         |
         v
  extract_zip_file            →  extracts zip locally, returns namelist
         |
         v
  update_database_records     →  inserts all items/files into DB
    ├── get_items_titles_and_parents_data
    │     ├── remove_slash
    │     └── get_index_of_parent
    ├── get_files_data
    └── update_files_parent   →  sets parent FK on each DB record
         |
         v
  upload_files_to_s3          →  uploads each extracted file to S3
         |
         v
  update_upload_status        →  marks root folder as is_uploaded=True
         |
         v
  cleanup_temp_files          →  deletes ./work_dir/<uuid>/
```

---

## Key Concepts

**`input_item_id`** — the DB item ID of the zip file the user wants to extract.

**`output_item_id`** — the DB item ID of a root folder item that must already exist in the database before the flow runs. The flow populates this folder's children.

**`work_dir`** — a module-level constant (`"./work_dir"`). Each flow run creates a unique UUID subdirectory inside it, so concurrent runs do not collide.

**Parent-child mapping** — the zip's internal path structure is translated into DB parent foreign keys. Each file/folder record has a `parent` field pointing to its containing folder's item ID.
