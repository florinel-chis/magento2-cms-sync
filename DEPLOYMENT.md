# Deployment Guide - Magento CMS Sync Tool

## Prerequisites

- Python 3.11+
- Node.js 16+
- nginx or Apache (for reverse proxy)
- systemd (for service management)
- SSL certificate (recommended)

## Production Deployment Steps

### 1. Backend Deployment

#### Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### Configure Environment
Create `.env` file:
```bash
cp .env.example .env
# Edit .env with production values
```

Important production settings:
- Set `DEBUG=false`
- Generate a secure `SECRET_KEY`
- Configure `CORS_ORIGINS` with your frontend URL
- Consider using PostgreSQL instead of SQLite for production

#### Create systemd Service
Create `/etc/systemd/system/cmssync-backend.service`:
```ini
[Unit]
Description=Magento CMS Sync Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/cmssync/backend
Environment="PATH=/opt/cmssync/backend/venv/bin"
ExecStart=/opt/cmssync/backend/venv/bin/gunicorn main:app \
          --workers 4 \
          --worker-class uvicorn.workers.UvicornWorker \
          --bind 127.0.0.1:8000 \
          --access-logfile /var/log/cmssync/backend-access.log \
          --error-logfile /var/log/cmssync/backend-error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable cmssync-backend
sudo systemctl start cmssync-backend
```

### 2. Frontend Deployment

#### Build Production Bundle
```bash
cd frontend
npm install
npm run build
```

#### Serve Static Files
The build output in `frontend/build` can be served by nginx or any static file server.

### 3. Nginx Configuration

Create `/etc/nginx/sites-available/cmssync`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    # Frontend
    root /opt/cmssync/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/cmssync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Database Backup

Set up automated backups for the SQLite database:
```bash
# Create backup script at /opt/cmssync/backup.sh
#!/bin/bash
BACKUP_DIR="/opt/cmssync/backups"
DB_PATH="/opt/cmssync/backend/cmssync.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_PATH "$BACKUP_DIR/cmssync_$TIMESTAMP.db"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "cmssync_*.db" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/cmssync/backup.sh
```

### 5. Monitoring

#### Application Logs
- Backend: `/var/log/cmssync/backend-*.log`
- Nginx: `/var/log/nginx/access.log` and `error.log`

#### Health Monitoring
Set up monitoring with the health check endpoint:
```bash
curl http://localhost:8000/api/health
```

Consider using tools like:
- Prometheus + Grafana for metrics
- ELK stack for log aggregation
- Uptime monitoring services

### 6. Security Hardening

1. **API Token Encryption**: Implement encryption for stored API tokens
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Ensure all inputs are properly validated
4. **HTTPS Only**: Force all traffic through HTTPS
5. **Firewall Rules**: Only expose necessary ports (80, 443)

### 7. Performance Optimization

1. **Database**: Consider migrating to PostgreSQL for better performance
2. **Caching**: Implement Redis for caching frequently accessed data
3. **CDN**: Use a CDN for static assets
4. **Compression**: Enable gzip compression in nginx
5. **Connection Pooling**: Configure database connection pooling

## Docker Deployment (Alternative)

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cmssync
      - CORS_ORIGINS=["https://your-domain.com"]
    depends_on:
      - db
    volumes:
      - ./backend/data:/app/data
    restart: always

  frontend:
    build: ./frontend
    environment:
      - REACT_APP_API_URL=https://your-domain.com
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: always

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cmssync
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

## Maintenance

### Regular Tasks
1. Monitor disk space for JSON data storage
2. Clean up old sync history records
3. Update dependencies regularly
4. Review and rotate logs
5. Test backup restoration procedures

### Scaling Considerations
1. **Horizontal Scaling**: Use a load balancer for multiple backend instances
2. **Database Scaling**: Implement read replicas for heavy read loads
3. **Storage Scaling**: Consider object storage (S3) for JSON data files
4. **Queue System**: Add Celery/RabbitMQ for async processing of large syncs