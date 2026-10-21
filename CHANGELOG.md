# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Magento API tokens are encrypted at rest (Fernet) with the required `ENCRYPTION_KEY`
  setting; `backend/scripts/encrypt_existing_tokens.py` converts tokens stored by earlier
  versions. Request validation on the compare and sync endpoints.
- `LICENSE` file (MIT).
- Compare pages: an "Only in Destination" counter and filter; Ctrl/Cmd+K focuses the search box.
- Backend test suite (pytest) running the application against a fake Magento 2.4 REST API
  (`backend/tests/magento_stub`), with a GitHub Actions workflow. The fake also runs as a
  standalone server for trying the UI without Magento.
- User documentation: user guide, configuration reference, API reference, architecture,
  deployment and troubleshooting guides; screenshots captured from the UI against two real
  Magento 2.4.9 instances.

### Changed
- `POST /api/instances/` returns 201 and `DELETE /api/instances/{id}` returns 204.
- Docker Compose is the supported deployment; the deployment guide covers only that path.
- The API never returns Magento tokens any more; the edit form keeps the stored token when
  the field is left blank. Deleting an instance removes the sync history on both sides.
- Sync runs left unfinished by a backend restart are marked failed at the next start instead
  of staying "in progress" forever.
- "Push to Destination" in the diff viewer waits for the sync to finish and reports the real
  outcome. The header checkbox on the compare pages selects the syncable items of the
  current filter instead of the whole comparison.
- History loads every run (previously the newest 100), treats the end date as inclusive,
  rounds durations, and exports properly quoted CSV. The Sync page refreshes without
  flashing a full-page spinner.
- API error messages from validation failures are readable instead of "[object Object]";
  the unused login redirect on 401 responses is gone.
- Unknown keys in `backend/.env` are ignored instead of aborting startup.
- Comparison compares Magento's `active` flag and no longer compares `creation_time` and
  `update_time`, which differ between any two Magento servers.
- `CORS_ORIGINS` accepts a comma-separated list (a JSON list still works).
- Docker: the backend image no longer runs a non-existent Alembic migration at startup, has
  a working health check, and both compose files keep the database and the snapshots
  together under `/app/data`.
- Frontend: the "Same" counter no longer includes items that differ; block rows show the
  real active flag; environment examples list only the variables the code reads.

### Removed
- The unused `API_PREFIX` setting and the never-used `comparison_cache` table.
- Generated code-review reports, planning documents and personal tooling configuration
  from the repository; `CONTRIBUTING.md` now holds the development guide.

### Fixed
- The frontend's data-snapshot helper called an endpoint that does not exist.
- Sync created items with the source's internal id in the payload, which on Magento updates
  (or overwrites) the destination entity with that id instead of creating one, and block
  updates failed on a `block_id` field Magento never returns.
- The frontend did not compile: six TypeScript errors and a duplicated `react-hooks` ESLint
  plugin.
- The sync wizard jumped back to its first step as soon as a sync finished, hiding the result.
- The documented `REACT_APP_API_URL` value lacked the `/api` prefix and broke every request.
