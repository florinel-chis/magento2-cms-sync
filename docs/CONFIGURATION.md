# Configuration Reference

Every setting below is read by the code as described; nothing else is configurable through
the environment. Defaults are the values in `backend/config.py` and `frontend/src/services/api.ts`.

## Backend

Settings are read from environment variables, or from a `backend/.env` file (environment
variables win). Names are case-insensitive. `backend/.env.example` lists them all.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./cmssync.db` | SQLAlchemy URL of the application database (instances, snapshot metadata, sync history). The async driver prefix is required: a plain `sqlite:///` URL fails at startup. The path is relative to the backend's working directory. |
| `DATA_DIR` | `data` | Base data directory; created at startup if missing. |
| `INSTANCES_DATA_DIR` | `data/instances` | Where the cached snapshots are written: one `blocks.json` and one `pages.json` per instance, in `INSTANCES_DATA_DIR/<instance id>/`. Created on demand. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | Browser origins allowed to call the API, comma-separated (a JSON list such as `["https://a","https://b"]` is also accepted). Only relevant when the UI is served from a different origin than the API; the Docker image and the nginx example proxy `/api` on the same origin. |
| `MAGENTO_TIMEOUT` | `30` | Timeout in seconds for each request to a Magento instance. |
| `MAGENTO_RETRY_ATTEMPTS` | `3` | How many times a Magento request is retried after a 5xx response or a network error. 4xx responses are not retried. |
| `MAGENTO_RETRY_DELAY` | `1` | Base delay in seconds between retries; the n-th retry waits `MAGENTO_RETRY_DELAY × n`. |
| `JSON_INDENT` | `2` | Indentation of the snapshot JSON files. |
| `JSON_ENSURE_ASCII` | `false` | Escape non-ASCII characters in the snapshot files. |

Not configurable: the log level (INFO) and the log files (see below), the Magento search
page size (100 items per request), and the API port (set it on the `uvicorn` command line).

### Files the backend writes

All paths are relative to the backend's working directory unless the variables above make
them absolute.

| Path | Content |
|---|---|
| `cmssync.db` | SQLite database (tables `instances`, `data_snapshots`, `sync_history`). Created on first start; there is no migration tooling. |
| `data/instances/<id>/blocks.json`, `pages.json` | Cached CMS snapshots, exactly as returned by Magento. |
| `logs/app.log` | Application log, rotated at 10 MB, 5 files kept. |
| `logs/errors.log` | Errors only, same rotation. |

Uvicorn's access log goes to standard output.

## Frontend

The frontend is a Create React App build; variables are baked in at build time.

| Variable | Default | Description |
|---|---|---|
| `REACT_APP_API_URL` | `/api` | Base URL of the backend API, **including** the `/api` prefix. Leave it unset when the UI and the API share an origin (Docker image, nginx example, dev-server proxy). Set it, for example `https://sync.example.com/api`, only when the API lives on another origin; then add the UI origin to the backend's `CORS_ORIGINS`. |
| `PORT` | `3000` | Dev-server port (`npm start` only). |

In development, `package.json` sets `"proxy": "http://localhost:8000"`, so the dev server
forwards `/api` to a local backend.

Requests time out after 30 seconds (hard-coded in `frontend/src/services/api.ts`).

## Docker Compose variables

`docker-compose.yml` (bind-mounts `./backend/data`, publishes the API on 8000 and the UI
on 80) has no variables. `docker-compose.prod.yml` reads:

| Variable | Default | Description |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost` | Passed to the backend; only needed for cross-origin API use. |
| `PORT` | `80` | Host port published for the UI. |

Both compose files set `DATABASE_URL`, `DATA_DIR` and `INSTANCES_DATA_DIR` so that the
database and the snapshots live together under `/app/data` in the container.
