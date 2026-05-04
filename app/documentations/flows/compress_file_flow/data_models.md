# Data Models

All models are Pydantic `BaseModel` classes defined in `compress_file_flow.py`.

---

## `FilePathsAndUrlsResponse`

Output of `get_file_paths_and_urls`. Contains two parallel lists — local relative paths and their corresponding S3 keys — built by recursively traversing the folder tree in the database.

```python
class FilePathsAndUrlsResponse(BaseModel):
    file_paths: List[str]
    file_urls: List[str]
```

| Field        | Type        | Description |
|--------------|-------------|-------------|
| `file_paths` | `List[str]` | Relative paths for every entry (root folder first). Folder entries end with `/`. |
| `file_urls`  | `List[str]` | S3 key for each entry. Empty string `""` for folders (nothing to download). |

The two lists are always the same length and are index-aligned: `file_paths[i]` corresponds to `file_urls[i]`.

**Example:**

For a folder `project` containing `folder1/` and `folder1/design.vcp`:

```python
FilePathsAndUrlsResponse(
    file_paths = ["project/", "project/folder1/", "project/folder1/design.vcp"],
    file_urls  = ["",         "",                 "uuid-a.vcp"],
)
```

---

## `PrepareCompressionResponse`

Output of `prepare_compression`. Contains everything the rest of the flow needs: the path/URL lists, all local filesystem paths, and the output S3 key.

```python
class PrepareCompressionResponse(BaseModel):
    file_paths: List[str]
    file_urls: List[str]
    file_download_path: str
    directory_to_zip: str
    compressed_zip_path: str
    output_file_url: str
```

| Field                 | Type        | Description | Example |
|-----------------------|-------------|-------------|---------|
| `file_paths`          | `List[str]` | Relative paths from `get_file_paths_and_urls`. | `["project/", "project/folder1/", ...]` |
| `file_urls`           | `List[str]` | S3 keys from `get_file_paths_and_urls`. | `["", "", "uuid-a.vcp"]` |
| `file_download_path`  | `str`       | Root local working directory for this run. | `./work_dir/f47ac10b` |
| `directory_to_zip`    | `str`       | The specific subfolder inside `file_download_path` that will be zipped. | `./work_dir/f47ac10b/project` |
| `compressed_zip_path` | `str`       | Local path where the output zip file will be written. | `./work_dir/f47ac10b/f47ac10b.zip` |
| `output_file_url`     | `str`       | S3 key under which the final zip will be uploaded. | `uuid-output.zip` |

> **Note:** `directory_to_zip` is derived from `file_paths[0]` — the first entry is always the root folder name. `compressed_zip_path` uses the same UUID as the working directory to guarantee a unique filename.
