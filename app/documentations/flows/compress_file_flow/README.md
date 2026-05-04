# Compress Zip Workflow

## Purpose

This workflow compresses a folder (and all its nested contents) stored in AWS S3 into a single zip file, saves the zip back to S3, updates the database, and cleans up temporary local files.

It is triggered when a user wants to compress a folder in their workspace into a downloadable zip. The workflow recursively traverses the folder's children in the database, downloads each file from S3 while preserving the original directory structure, zips them locally, and uploads the result.

---

## Source File

`api_server/app/flows/compress_file_flow.py`

---

## Documentation Index

| File | Contents |
|------|----------|
| [data_models.md](data_models.md) | Pydantic models used across the flow |
| [helper_functions.md](helper_functions.md) | Plain utility functions (no Prefect decoration) |
| [tasks.md](tasks.md) | Individual Prefect tasks |
| [flow.md](flow.md) | Main Prefect flow and execution order |
| [example.md](example.md) | Full end-to-end walkthrough with concrete data |

---

## High-Level Diagram

```
[Inputs: input_item_id (folder to zip), output_item_id (pre-created zip file item in DB)]
         |
         v
  prepare_compression         →  resolves file_paths, file_urls, local paths, output S3 key
    └── get_file_paths_and_urls   (plain async function — recursive DB traversal)
         |
         v
  download_s3_objects         →  downloads every file from S3, rebuilding folder structure locally
    └── download_file_from_s3     (plain function — per-file download helper)
         |
         v
  zip_directory               →  zips the local folder tree into a single .zip file
         |
         v
  upload_zip_to_s3            →  uploads the .zip to S3 under the output file's key
         |
         v
  update_upload_status        →  marks output item as is_uploaded=True in DB
         |
         v
  cleanup_temp_files          →  deletes the entire local working directory
```

---

## Key Concepts

**`input_item_id`** — the DB item ID of the folder the user wants to compress.

**`output_item_id`** — the DB item ID of a zip file item that must already exist in the database before the flow runs. The flow writes the resulting zip to this item's S3 key.

**`work_dir`** — a module-level constant (`"./work_dir"`). Each flow run creates a unique UUID subdirectory inside it, so concurrent runs do not collide.

**Recursive traversal** — `get_file_paths_and_urls` walks the DB parent-child tree depth-first to reconstruct the full path list and corresponding S3 keys, mirroring the folder hierarchy that will be recreated locally before zipping.

**Path list convention** — folder entries have a trailing `/` and an empty S3 key (`""`). File entries have no trailing `/` and a non-empty S3 key. This is used to decide whether to create a directory or download a file.
