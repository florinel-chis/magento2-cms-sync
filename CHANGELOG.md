# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Backend test suite (pytest) running the application against a fake Magento 2.4 REST API
  (`backend/tests/magento_stub`), with a GitHub Actions workflow. The fake also runs as a
  standalone server for trying the UI without Magento.
- User documentation: user guide, configuration reference, API reference, architecture,
  deployment and troubleshooting guides; screenshots captured from the UI against two real
  Magento 2.4.9 instances.

### Changed
- Comparison compares Magento's `active` flag and no longer compares `creation_time` and
  `update_time`, which differ between any two Magento servers.
- `CORS_ORIGINS` accepts a comma-separated list (a JSON list still works).
- Docker: the backend image no longer runs a non-existent Alembic migration at startup, has
  a working health check, and both compose files keep the database and the snapshots
  together under `/app/data`.
- Frontend: the "Same" counter no longer includes items that differ; block rows show the
  real active flag; environment examples list only the variables the code reads.

### Fixed
- Sync created items with the source's internal id in the payload, which on Magento updates
  (or overwrites) the destination entity with that id instead of creating one, and block
  updates failed on a `block_id` field Magento never returns.
- The frontend did not compile: six TypeScript errors and a duplicated `react-hooks` ESLint
  plugin.
- The sync wizard jumped back to its first step as soon as a sync finished, hiding the result.
- The documented `REACT_APP_API_URL` value lacked the `/api` prefix and broke every request.
