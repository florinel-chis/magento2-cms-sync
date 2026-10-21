# Deployment

Two supported ways to run Magento CMS Sync: Docker Compose, or a manual install with
uvicorn behind nginx. Either way, read [Access control](#access-control) first: the
application has no login of its own.

## Docker Compose

Both compose files build two images: the backend (`python:3.11-slim`, uvicorn on port 8000)
and the frontend (static build served by nginx, which proxies `/api` to the backend).

### Development stack: `docker-compose.yml`

```bash
docker compose up -d --build
```

- UI on http://localhost, API on http://localhost:8000 (also reachable through the UI origin
  as `/api`).
- The database and the snapshots are bind-mounted from `./backend/data`.

### Production stack: `docker-compose.prod.yml`

```bash
PORT=8080 CORS_ORIGINS=http://localhost:8080 docker compose -f docker-compose.prod.yml up -d --build
```

- Publishes only the UI, on `PORT` (default 80). The API is reachable through `/api` on that
  port; it is not published separately.
- Data lives in the named volume `backend-data` (mounted at `/app/data`).
- `CORS_ORIGINS` only matters if something other than the bundled UI calls the API from a
  browser.

### Upgrading

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Tables are created automatically on first start. There is no migration tooling: a release
that changes an existing table documents the manual step in the changelog.

### Backups

Everything is under `/app/data` in the backend container: `cmssync.db` and `instances/`.

```bash
# copy the data directory out of the running container
docker compose -f docker-compose.prod.yml cp backend:/app/data ./backup-$(date +%F)
```

Stop the backend first, or accept that a sync running at that moment may be half-recorded.

## Manual installation

### Backend

```bash
sudo mkdir -p /opt/cmssync && sudo chown $USER /opt/cmssync
git clone https://github.com/florinel-chis/magento2-cms-sync.git /opt/cmssync
cd /opt/cmssync/backend
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env            # adjust DATABASE_URL / data dir / CORS_ORIGINS if needed
```

systemd unit, `/etc/systemd/system/cmssync-backend.service`:

```ini
[Unit]
Description=Magento CMS Sync backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/cmssync/backend
ExecStart=/opt/cmssync/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /opt/cmssync/backend
sudo systemctl daemon-reload && sudo systemctl enable --now cmssync-backend
curl http://127.0.0.1:8000/        # {"message":"Magento CMS Sync API","version":"1.0.0"}
```

Run a single uvicorn worker. Syncs are background tasks inside the process, and the SQLite
database is not meant for several writers.

### Frontend

```bash
cd /opt/cmssync/frontend
npm ci
npm run build                    # static files in build/
```

Leave `REACT_APP_API_URL` unset so the UI calls `/api` on its own origin.

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name sync.example.com;
    ssl_certificate     /etc/letsencrypt/live/sync.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sync.example.com/privkey.pem;

    # see "Access control" below
    auth_basic           "Magento CMS Sync";
    auth_basic_user_file /etc/nginx/cmssync.htpasswd;

    root /opt/cmssync/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;   # refreshes and syncs of large catalogs take a while
    }

    # optional: interactive API docs
    location /docs    { proxy_pass http://127.0.0.1:8000/docs; }
    location /openapi.json { proxy_pass http://127.0.0.1:8000/openapi.json; }
}
server {
    listen 80;
    server_name sync.example.com;
    return 301 https://$host$request_uri;
}
```

## Access control

The UI and the API have no authentication. Anyone who can reach them can read the stored
Magento tokens and write to the connected stores. At minimum:

- Serve the application only on a private network or VPN, or
- Require a login at the reverse proxy (`htpasswd -c /etc/nginx/cmssync.htpasswd admin` for
  the nginx example above), and
- Use HTTPS between the browser and the tool, and between the tool and Magento.

Give each Magento token only the four ACL resources the tool needs (see the User Guide).

## Health and monitoring

- `GET /` on the backend returns a JSON greeting; the Docker image uses it as its health
  check (`docker ps` shows `healthy`).
- Backend logs: `backend/logs/app.log` and `backend/logs/errors.log` (rotated at 10 MB, 5
  files kept), relative to the working directory, plus uvicorn's access log on stdout
  (`docker compose logs backend`, or `journalctl -u cmssync-backend`).
- Disk: snapshots are small JSON files, but one per instance and type is rewritten on each
  refresh; the SQLite database grows with the sync history.
