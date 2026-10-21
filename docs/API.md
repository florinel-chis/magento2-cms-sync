# REST API Reference

The backend is a FastAPI application. Interactive documentation generated from the code is
served at `/docs` (Swagger UI) and `/redoc`, and the OpenAPI document at `/openapi.json`.
This page describes the same endpoints with the behaviour that matters when scripting
against them.

- Base path: `/api`. Collection routes end with a slash (`/api/instances/`); the un-slashed
  form answers with a 307 redirect.
- Bodies and responses are JSON. Validation errors return 422 with FastAPI's `detail` array;
  application errors return `{"detail": "<message>"}` with the status codes listed below.
- There is no authentication on the API itself.

`GET /` returns `{"message": "Magento CMS Sync API", "version": "1.0.0"}` and doubles as the
health check.

## Instances

An instance is a Magento store: `{id, name, url, is_active, created_at, updated_at}`. The
API token is write-only: it is accepted on create and update but never returned.

| Method and path | Description |
|---|---|
| `GET /api/instances/?skip=0&limit=100` | List instances. |
| `POST /api/instances/` | Create. Body: `{"name", "url", "api_token", "is_active": true}`. `url` must be an absolute http(s) URL. 400 `Instance with this name already exists`. |
| `GET /api/instances/{id}` | One instance. 404 `Instance not found`. |
| `PUT /api/instances/{id}` | Partial update; any of `name`, `url`, `api_token`, `is_active`. Omit `api_token` to keep the stored one. 400 on a name clash. |
| `DELETE /api/instances/{id}` | Deletes the instance, its snapshot files and every sync history run it took part in, as source or destination. Returns `{"message": "Instance deleted successfully"}`. |
| `POST /api/instances/{id}/test` | Calls Magento's `store/storeViews`. Returns `{"success", "message", "version": null, "store_views": [...]}`; `success` is false with `Authentication failed. Please check your API token.` on 401, `HTTP error: <code>` on other HTTP errors, or `Connection failed: <reason>`. Always HTTP 200. |
| `GET /api/instances/{id}/data-snapshots` | `{"instance_id", "blocks": {"count", "last_updated"} \| null, "pages": ...}` for the latest snapshots. |
| `GET /api/instances/data-snapshots/all` | The same for every instance, keyed by instance id (`lastUpdated` camel-cased). |

Example:

```bash
curl -s -X POST http://localhost:8000/api/instances/ -H 'Content-Type: application/json' \
  -d '{"name":"Staging","url":"https://staging.example.com","api_token":"<token>"}'
curl -s -X POST http://localhost:8000/api/instances/1/test
```

## Comparison

| Method and path | Description |
|---|---|
| `POST /api/compare/refresh/{id}?data_type=blocks\|pages` | Fetch that content type from Magento and replace the snapshot. Returns `{"message", "snapshot_id", "item_count", "created_at"}`. 502 `Failed to fetch data from Magento: <reason>` when Magento cannot be read. |
| `POST /api/compare/blocks` | Compare blocks. Body: `{"source_instance_id", "destination_instance_id", "force_refresh": false}`. With `force_refresh` true, both snapshots are refreshed first; otherwise snapshots are used and only fetched when missing. |
| `POST /api/compare/pages` | Same for pages. |
| `POST /api/compare/diff` | Field-by-field diff of one item. Body: `{"source_instance_id", "destination_instance_id", "data_type", "identifier"}`. 400 when a snapshot is missing (`No data snapshot found for ... instance. Please run comparison first.`), 404 when the identifier exists on neither side. |

A comparison result:

```json
{
  "source_instance": {...}, "destination_instance": {...}, "data_type": "pages",
  "total_source": 47, "total_destination": 45,
  "exists_in_both": 39, "missing_in_destination": 3, "missing_in_source": 1, "different": 3,
  "items": [
    {"identifier": "shipping-policy", "title": "Shipping Policy",
     "source_status": "different", "destination_status": "different",
     "source_data": {...magento page...}, "destination_data": {...},
     "differences": ["content"]}
  ],
  "compared_at": "2026-10-21T18:17:27Z"
}
```

`exists_in_both` counts every identifier present on both sides, including the `different`
ones. Statuses are `exists`, `missing` or `different` (the latter on both sides at once).
`source_data` and `destination_data` are the raw Magento objects from the snapshots.

A diff result lists every compared field (see the User Guide) with
`{"field_name", "source_value", "destination_value", "is_different"}`, plus
`source_stores` and `destination_stores` (empty on stock Magento).

## Sync

Request body shared by preview and execution:

```json
{
  "source_instance_id": 1, "destination_instance_id": 2, "data_type": "pages",
  "items": [
    {"identifier": "shipping-policy", "action": "update"},
    {"identifier": "size-guide", "action": "create", "fields_to_sync": null}
  ],
  "store_view_mapping": null
}
```

- `action` is `create` (item must be absent in the destination) or `update` (item must
  exist there); a mismatch yields the per-item error `Invalid action or item state`.
- `fields_to_sync` (updates only): copy only these fields from the source; the rest of the
  destination item is kept. Omit it to copy all content fields.
- `store_view_mapping` maps source store ids to destination store ids (`{"1": "2"}`). It only
  has an effect on Magento installs whose API exposes `store_id`.

| Method and path | Description |
|---|---|
| `POST /api/sync/preview` | No changes made. Returns `{"items": [{"identifier", "action", "source", "destination", "result"}], "total_changes", "creates", "updates"}` where `result` is the payload that would be sent. 400 when the source has no snapshot. |
| `POST /api/sync/blocks`, `POST /api/sync/pages` | Start a sync; `data_type` must match the path (400 `Data type mismatch`). Returns immediately with `status: "pending"` and a `sync_id`; the work runs in the background. |
| `GET /api/sync/status/{sync_id}` | `{"sync_id", "status", "items_synced", "items_failed", "started_at", "completed_at", "details": [{"identifier", "action", "success", "message", "error"}], "error_message"}`. `status` is `pending`, `in_progress`, `completed` or `failed`. 404 `Sync operation not found`. |

Execution reads the source items from the source snapshot and the current destination items
live from Magento, strips ids and timestamps from the payload, then `POST`s creates and
`PUT`s updates to Magento. `completed` means the run finished; look at `items_failed` and the
`details` for individual failures (each carries Magento's message). `failed` means the run
itself aborted, for example when the source snapshot was missing or the destination could
not be listed; `error_message` says why. After a completed run the destination snapshot is
refreshed. Runs that were still `pending` or `in_progress` when the backend process stopped
are marked `failed` with the message `Abandoned: the backend restarted while this sync was
running` at the next start.

```bash
curl -s -X POST http://localhost:8000/api/sync/pages -H 'Content-Type: application/json' -d @sync.json
curl -s http://localhost:8000/api/sync/status/12
```

## History

| Method and path | Description |
|---|---|
| `GET /api/history/` | Sync runs, newest first. Query: `skip` (default 0), `limit` (default 50, max 100), `status`, `sync_type` (`blocks`/`pages`), `source_instance_id`, `destination_instance_id`, `start_date`, `end_date` (ISO datetimes, compared with `started_at`). Returns `{"items": [...], "total", "skip", "limit"}`; each item has the instance names, counts, timestamps, `error_message` and `duration` in seconds (null while running). |
| `GET /api/history/statistics?period=today\|week\|month\|all` | `{"period", "total_syncs", "completed_syncs", "failed_syncs", "active_syncs", "success_rate", "total_items_synced", "total_items_failed", "active_sync_details": [...]}`. `today` starts at 00:00 UTC. |
| `GET /api/history/{sync_id}` | One run with `sync_details`: the per-item `results` after completion (the requested `items` before). 404 `Sync history not found`. |

## Diagnostics

`GET /api/test/test-logging` writes a test message to the backend's standard output and
returns `{"message": "Check console for logs"}`. It exists for debugging the logging setup.
