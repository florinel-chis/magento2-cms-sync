# Troubleshooting Guide - Magento CMS Sync Tool

## Common Issues and Solutions

### Backend Issues

#### 1. Backend won't start
**Error**: `ModuleNotFoundError`
```bash
# Solution: Activate virtual environment and install dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Database errors
**Error**: `sqlite3.OperationalError: database is locked`
```bash
# Solution: Ensure only one instance is running
pkill -f "uvicorn main:app"
# Then restart
uvicorn main:app --reload
```

#### 3. API Token Authentication Fails
**Error**: `401 Unauthorized` when testing connection
- Verify the API token is correct
- Check if token has necessary permissions in Magento
- Ensure the Magento instance URL is correct (with /rest prefix if needed)

#### 4. CORS Errors
**Error**: `Access to XMLHttpRequest blocked by CORS policy`
```python
# Solution: Update backend/config.py
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "your-frontend-url"]
```

### Frontend Issues

#### 1. Frontend build fails
**Error**: `npm ERR! peer dep missing`
```bash
# Solution: Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 2. Blank page or React errors
```bash
# Check browser console for errors
# Clear browser cache
# Check if API URL is correct in .env
```

#### 3. API calls failing
**Error**: `Network Error` or `ERR_CONNECTION_REFUSED`
- Ensure backend is running on port 8000
- Check proxy configuration in package.json
- Verify REACT_APP_API_URL in .env

### Magento Integration Issues

#### 1. Empty data when refreshing
**Possible causes**:
- API token lacks permissions
- Incorrect store view
- No CMS content in Magento instance

**Debug steps**:
```bash
# Test Magento API directly
curl -X GET "https://your-magento.com/rest/V1/cmsBlock/search" \
  -H "Authorization: Bearer your-token"
```

#### 2. Sync failures
**Error**: `Failed to create/update content`
- Check Magento error logs
- Verify user has write permissions
- Ensure required fields are not missing

### Data Storage Issues

#### 1. Disk space issues
```bash
# Check disk usage
du -sh backend/data/

# Clean old snapshots (careful!)
find backend/data/instances -name "*.json" -mtime +30 -delete
```

#### 2. JSON parsing errors
**Error**: `JSONDecodeError`
- Check if JSON files are corrupted
- Delete the specific snapshot and refresh data

### Performance Issues

#### 1. Slow comparison
**Symptoms**: Comparison takes too long
- Ensure data is cached (refresh if needed)
- Check network latency to Magento
- Consider pagination for large datasets

#### 2. High memory usage
```bash
# Monitor memory
top -p $(pgrep -f "uvicorn main:app")

# Increase Python memory limit if needed
```

### Debugging Tools

#### 1. Enable debug logging
```python
# backend/config.py
LOG_LEVEL = "DEBUG"
```

#### 2. Check API documentation
Visit http://localhost:8000/docs for interactive API testing

#### 3. Database inspection
```bash
# Open SQLite database
sqlite3 backend/cmssync.db
.tables
.schema instances
```

#### 4. Network debugging
```bash
# Monitor API calls
tail -f backend/server.log

# Check port usage
lsof -i :8000
lsof -i :3001
```

### Quick Fixes

#### Reset everything
```bash
# Stop all services
pkill -f "uvicorn main:app"
pkill -f "react-scripts"

# Clear data (WARNING: deletes all data)
rm -rf backend/cmssync.db
rm -rf backend/data/instances/*

# Restart
./start-dev.sh
```

#### Recreate virtual environment
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Force refresh frontend
```bash
cd frontend
rm -rf node_modules/.cache
npm start
```

### Getting Help

1. Check logs:
   - Backend: `backend/server.log`
   - Frontend: Browser console (F12)
   - System: `/var/log/syslog` or journalctl

2. Run health check:
   ```bash
   ./check-health.sh
   ```

3. Test individual components:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:3001
   - Database: `sqlite3 backend/cmssync.db`

4. Common commands:
   ```bash
   # Check if services are running
   ps aux | grep -E "uvicorn|react"
   
   # Check network connections
   netstat -tuln | grep -E "8000|3001"
   
   # View recent logs
   tail -n 100 backend/server.log
   ```

### Reporting Issues

When reporting issues, please include:
1. Error messages (full stack trace)
2. Steps to reproduce
3. Environment details (OS, Python version, Node version)
4. Output from `./check-health.sh`
5. Relevant log files