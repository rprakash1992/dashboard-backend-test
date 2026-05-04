# VCollab Enterprise Dashboard — API Server

FastAPI backend server with SQLAlchemy, PostgreSQL, and SQLite.

## Prerequisites

- Python 3.10+
- PostgreSQL instance (for the main dashboard database)

---

## Installation

```bash
cd api_server
python -m venv .venv
```

Activate the virtual environment:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

See [`.env.example`](.env.example) for all available variables.

The `MODE` variable controls the API route prefix:
- `local` — API is served at `/api/v1` (Traefik strips the `/server` prefix in local Docker setup)
- `production` — API is served at `/server/api/v1` (AWS ALB routes `/server/*` to the backend)

---

## Development

### Local dev server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server starts at [http://localhost:8000](http://localhost:8000).

### Dev server inside Docker

```bash
docker build -f Dockerfile_dev -t vcollab-api-dev .
docker run --env-file .env -p 8000:80 vcollab-api-dev
```

`Dockerfile_dev` runs uvicorn with `--reload` on port 80 inside the container.

---

## Production Build

```bash
docker build -f Dockerfile -t vcollab-api .
docker run --env-file .env -p 8000:80 vcollab-api
```

The production `Dockerfile` uses a multi-stage build with `python:3.10-slim` and runs 4 uvicorn workers.

---

## API Documentation

FastAPI auto-generates interactive docs when the server is running:

| URL | Description |
|---|---|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/health` | Health check — returns `{"status": "ok"}` |

---

## API Routes

All routes are prefixed with `/api/v1` (local) or `/server/api/v1` (production).

| Tag | Description |
|---|---|
| Views | Saved views / viewport states |
| Files | File metadata and management |
| File-Upload | File upload handling |
| Projects | Project CRUD |
| Project-Schemas | JSON schemas associated with projects |
| Items | Items within projects |
| Jobs | Background job tracking |
| Reports | Report generation and retrieval |
| Tags | Tagging system |
| Workspaces | Workspace management |
| User-Profiles | User profile data |
| Chat | AI chat (OpenAI integration) |

---

## Project Structure

```
api_server/
├── app/
│   ├── api/
│   │   ├── router.py          # Top-level API router
│   │   └── routes/            # One file per route group
│   ├── core/
│   │   ├── config.py          # Settings and env var loading
│   │   ├── dashboard_database.py  # PostgreSQL engine and session
│   │   ├── sqlite_database.py     # SQLite engine and session
│   │   └── dependencies.py    # FastAPI dependency injection
│   ├── models/                # SQLAlchemy ORM models
│   └── middlewares/           # Custom middleware (e.g. user info)
├── main.py                    # App entry point
├── requirements.txt
├── Dockerfile                 # Production image (multi-stage, 4 workers)
├── Dockerfile_dev             # Dev image (single worker, --reload)
└── .env.example               # Environment variable reference
```

---

## Databases

The server uses two databases:

- **PostgreSQL** (`DASHBOARD_DATABASE_URL`) — main application data (projects, files, jobs, etc.)
- **SQLite** (`test.db`) — lightweight local storage for auxiliary data

Both schemas are created automatically on startup via SQLAlchemy `create_all`.


## Building backend.exe
   backend.exe is used by electron app.

- Run `pyinstaller backend.spec`

   It will create **/build** and **/dist** folders.