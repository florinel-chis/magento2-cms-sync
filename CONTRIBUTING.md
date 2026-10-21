# Contributing

Thanks for helping improve Magento CMS Sync. This guide covers the development setup, the
conventions the code follows, and how changes get reviewed and released.

## Development setup

Requirements: Python 3.11+, Node.js 18+, and optionally Docker. No Magento installation
is needed for development: the test suite runs against a fake Magento REST API.

```bash
# backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
export ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
uvicorn main:app --reload --port 8000        # http://localhost:8000/docs

# frontend (in a second shell)
cd frontend
npm install
PORT=3001 npm start                          # proxies /api to the backend
```

A fake Magento for trying the UI without a real store:

```bash
cd backend
python -m tests.magento_stub --port 8081 --token secret --seed demo        # source
python -m tests.magento_stub --port 8082 --token secret --seed demo-dest   # destination
```

Register both on the Instances page with token `secret`. See
`backend/tests/magento_stub/README.md` for what the fake reproduces.

## Project layout

```
backend/
  api/            FastAPI routers (thin controllers)
  services/       comparison rules, sync orchestration, snapshot storage
  integrations/   Magento REST client (httpx)
  models/         SQLAlchemy models and Pydantic schemas
  tests/          pytest suite and the fake Magento (tests/magento_stub)
frontend/src/
  pages/          one component per route
  components/     diff viewer, sync wizard, dialogs, layout
  services/       API client and per-resource services
  store/          Zustand state
  types/          shared TypeScript interfaces
docs/             user and operator documentation
doc/              screenshots used by the README
```

The behaviour of the application is described in `docs/ARCHITECTURE.md`; read it before
changing the comparison or sync rules.

## Conventions

### Python

- Type hints on every function, including return types.
- All I/O is asynchronous: `httpx` for HTTP, `aiofiles` for files, the async SQLAlchemy
  session for the database. Never call blocking I/O inside an `async def`.
- Database writes are wrapped in `try`/`except`; on failure `await db.rollback()`, log with
  `exc_info=True`, then raise an `HTTPException`.
- Load related rows with `selectinload` instead of querying inside loops.
- Controllers stay thin: validation and business rules live in `services/`.
- Settings are read only through `config.settings`; every new setting is documented in
  `docs/CONFIGURATION.md` and `backend/.env.example`.

### TypeScript

- `strict` mode, no `any`. Shapes that come from Magento follow the Magento REST output
  (see `types/index.ts`); shapes that come from the backend follow `backend/models/schemas.py`.
- Hooks list all their dependencies; use `useCallback`/`useMemo` for values passed down or
  computed from large lists.
- Read Zustand state through selectors (`useStore(state => state.x)`), not
  `useStore.getState()`.
- All HTTP calls go through `services/api.ts`; collection endpoints keep their trailing
  slash (`/instances/`, `/history/`).

### Magento specifics worth remembering

- Blocks and pages are matched by `identifier`. Stock Magento returns no `store_id`,
  `url_key`, `is_active`, `block_id` or `page_id`; the active flag is `active`.
- Magento rejects unknown input properties and saves whatever entity id the request body
  carries, so creates must not include an id and updates must use the destination's id.
- `creation_time` and `update_time` are server-generated and never compared.

## Tests

```bash
cd backend && python -m pytest          # unit, client and end-to-end tests against the fake Magento
cd frontend && npx tsc --noEmit         # type check
cd frontend && npm run build            # production build must succeed
```

Every change to comparison or sync behaviour needs a test in
`backend/tests/test_integrations/`. If the fake Magento does not model something you rely
on, extend it (and its README) rather than working around it in the test.

## Documentation

The documentation under `docs/` describes the current behaviour, not plans. When a change
alters behaviour, configuration, an endpoint or an error message, update the affected
document in the same pull request and add a line to `CHANGELOG.md` under *Unreleased*.
Screenshots in `doc/` are taken from the running UI.

## Branches, commits and pull requests

- Branch from `main`: `feature/<topic>`, `fix/<topic>` or `docs/<topic>`. Use short,
  descriptive names that say what the branch delivers.
- Commit messages follow the Conventional Commits style used in the history:
  `feat:`, `fix:`, `docs:`, `test:`, `chore:`, optionally with a scope such as
  `fix(sync):`. The body explains why, in plain language. Commits and pull requests carry
  no tool-generated attribution lines.
- Open a pull request against `main` with a clear title and a description that states the
  problem, the change and how it was verified. Tests and the type check must pass.
- Releases are tagged on `main` (`vX.Y.Z`) after moving the *Unreleased* changelog section
  under the new version.
