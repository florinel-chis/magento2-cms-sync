# Deployment

Magento CMS Sync is deployed with Docker Compose on a Linux host that runs Docker Engine
with the Compose plugin. The stack is two containers: the API (`backend`) and the web UI
(`frontend`, nginx serving the built interface and proxying `/api` to the API).

Before exposing it, read [Access control](#access-control): the application has no login
of its own.

## 1. Prepare the host

```bash
git clone https://github.com/florinel-chis/magento2-cms-sync.git /opt/cmssync
cd /opt/cmssync
```

Generate the key that encrypts Magento API tokens in the database and put it, with the
other settings, in a `.env` file next to the compose files (Compose reads it automatically):

```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

```dotenv
# /opt/cmssync/.env
ENCRYPTION_KEY=<the generated key>
PORT=8080                       # host port for the web UI (default 80)
```

Back the key up together with the data. Without it the stored tokens cannot be decrypted
and every instance has to be re-entered.

## 2. Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps        # backend must be "healthy"
```

The UI is on `http://<host>:<PORT>/`; the API is reachable through `/api` on the same
port and is not published separately. Data (SQLite database and cached snapshots) lives in
the named volume `backend-data`, mounted at `/app/data` in the API container.

`docker-compose.yml` is the development variant: it publishes the API on port 8000 as well
and bind-mounts `./backend/data` instead of using a volume.

## 3. Put it behind TLS and a login

Terminate HTTPS and require authentication in front of the UI port. With Caddy, which
obtains certificates automatically:

```caddyfile
sync.example.com {
    basic_auth {
        admin <hash from: caddy hash-password>
    }
    reverse_proxy 127.0.0.1:8080
}
```

Any reverse proxy works the same way (nginx, Traefik, a cloud load balancer): forward
everything to the UI port, enforce HTTPS, require a login or restrict by network.

## Upgrades

```bash
cd /opt/cmssync
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Database tables are created automatically; there is no migration tooling. A release that
changes an existing table documents the manual step in `CHANGELOG.md`.

Upgrading from a version that stored tokens unencrypted: after the first start with
`ENCRYPTION_KEY` set, encrypt the existing rows once:

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/encrypt_existing_tokens.py
```

## Backups

Back up two things: the data volume and the `.env` file holding `ENCRYPTION_KEY`.

```bash
docker compose -f docker-compose.prod.yml cp backend:/app/data ./backup-$(date +%F)
cp .env ./backup-$(date +%F)/
```

Take the copy while no sync is running, or stop the backend first.

## Health and logs

- `GET /` on the API returns a JSON greeting and is the container health check.
- `docker compose -f docker-compose.prod.yml logs -f backend` shows the request log;
  application logs are in `/app/logs/app.log` and `/app/logs/errors.log` inside the
  container (rotated at 10 MB, five files kept).

## Access control

The UI and the API have no users or authentication. Anyone who can reach them can read
the connected stores' content and write to them, and the API accepts tokens for new
instances. Keep the stack on a private network or behind a reverse proxy that requires a
login, use HTTPS, and give each Magento token only the four permissions listed in the
User Guide.

## Without Docker

The API is a standard ASGI application: any process supervisor can run
`uvicorn main:app --host 127.0.0.1 --port 8000` from `backend/` with the same environment
variables, and any web server can serve `frontend/build` (from `npm run build`) while
proxying `/api` to the API. This path is not maintained step by step; Docker Compose is the
supported deployment.
