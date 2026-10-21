# Troubleshooting

Symptoms are listed with the exact message the tool shows, the cause, and the fix.

## Starting the backend

**`The asyncio extension requires an async driver to be used`** at startup.
`DATABASE_URL` uses `sqlite:///`. It must be `sqlite+aiosqlite:///...`.

**`error parsing value for field "cors_origins"`** at startup.
You are running a version older than this one with a comma-separated `CORS_ORIGINS`; upgrade,
or use a JSON list (`["http://a","http://b"]`).

**`ModuleNotFoundError`**. The virtual environment is not active or dependencies are not
installed: `source venv/bin/activate && pip install -r requirements.txt`.

**Port already in use** (`npm start` says "Something is already running on port 3000").
Start the dev server with `PORT=3001 npm start`; 3001 is in the backend's default CORS list.

## The UI cannot reach the API

**Every page shows "Network error. Please check your connection."** or the browser console
shows 404s for `/instances`.
`REACT_APP_API_URL` is set without the `/api` suffix, or points at the wrong host. In
development leave it unset (the dev server proxies `/api` to port 8000); in production either
leave it unset and proxy `/api` on the same origin, or set it to the full API base including
`/api` and add the UI origin to `CORS_ORIGINS`.

**Browser console: "blocked by CORS policy".** The UI is served from an origin that is not
in `CORS_ORIGINS`. Add it (comma-separated) and restart the backend, or serve the UI and the
API from the same origin.

## Connecting to Magento

The messages below come from **Test Connection** on the Instances page.

**"Authentication failed. Please check your API token."**
Magento answered 401. Either the token is wrong, it expired (admin tokens expire; see the
User Guide), the user lost access, or on Magento 2.4.4+ an integration token is used while
*Allow OAuth Access Tokens to be used as standalone Bearer tokens* is disabled.

**"HTTP error: 404"**
The URL is not the Magento base URL. Use `https://shop.example.com`, not `.../rest` or
`.../rest/V1`, and not a storefront that is served by something other than Magento.

**"Connection failed: ..."**
Network, DNS or TLS problem between the tool's server and Magento. The reason is the raw
client error (for example a timeout after `MAGENTO_TIMEOUT` seconds).

**Refresh fails with "Failed to fetch data from Magento: ..."** (HTTP 502 from the API).
The connection test passes but the token lacks `Magento_Cms::block` or `Magento_Cms::page`,
or the store returned an error while paging. The reason after the colon is Magento's response.

## Comparing

**The comparison does not show content I just changed in Magento.**
Comparisons read the cached snapshots. Click the Blocks or Pages icon on the Instances page
to refresh that instance, then compare again.

**A page is listed once although Magento has several with that identifier** (one per store
view). Items are keyed by identifier; duplicates collapse. See the User Guide's limitations.

**Every item is "Different" right after a successful sync.**
Versions before this one compared Magento's creation and update timestamps, which differ
between servers. Upgrade; timestamps are no longer compared.

## Syncing

Per-item errors appear in the wizard's result step and in `GET /api/history/{sync_id}`.

**"A block identifier with the same properties already exists in the selected store."** or
**"Could not save the page: A page URL key for specified store already exists."**
Magento's uniqueness check. Usually the destination already has that identifier in another
store view, which the tool cannot see. Fix the duplicate in Magento or skip the item.

**"Source item not found: <identifier>"**
The source snapshot no longer contains the item (refreshed between compare and sync).
Compare again.

**"Invalid action or item state: create|update"**
The item was created or removed in the destination after the comparison, so "create" met an
existing item or "update" found none. Compare again.

**"Destination item has no id: <identifier>"**
The destination's API returned an item without `id`; this happens only with customised
Magento APIs. The item is skipped.

**Client error '401 Unauthorized' ...** in a per-item error, or a run that ends **failed**
with a 401 in `error_message`. The destination token expired or was revoked mid-run. Update
the token on the Instances page and run the sync again.

**A run stays "In Progress" or "Pending" forever.**
The backend was restarted while the sync ran; the row is never updated. Run the sync again.
To tidy the history:

```bash
sqlite3 backend/cmssync.db "UPDATE sync_history SET sync_status='failed',
  error_message='abandoned: backend restarted' WHERE sync_status IN ('pending','in_progress');"
```

**"Push to Destination" said success but the diff still shows differences.**
The button starts the sync in the background and reports that it was started. Wait a
moment, check History, and open the diff or compare again.

## Where to look

- Backend application log: `backend/logs/app.log`; errors only: `backend/logs/errors.log`.
- Request log: uvicorn's standard output (`docker compose logs backend`).
- Snapshots: `backend/data/instances/<instance id>/blocks.json` and `pages.json` are exactly
  what Magento returned; inspect them to understand a surprising comparison.
- Database: `sqlite3 backend/cmssync.db` with tables `instances`, `data_snapshots` and
  `sync_history`.
- Interactive API docs: `http://<backend>/docs`.
- Direct Magento check:
  `curl -H "Authorization: Bearer <token>" "https://shop.example.com/rest/V1/cmsPage/search?searchCriteria[pageSize]=1"`
