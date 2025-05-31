# Magento CMS Sync Tool - Technical Documentation

## Overview
This is a web-based tool for synchronizing CMS content (blocks and pages) between multiple Magento 2 instances. It provides a complete solution for content comparison, diff visualization, and synchronization with a modern React frontend and FastAPI backend.

## Key Technical Decisions

### Data Storage Strategy
As per the user's requirement: "pull data from the source and store that json. same for destination and compare based on stored json files, that can be refreshed instead of pulling data everytime the comparison is done"

- JSON files are stored in `backend/data/instances/{instance_id}/`
- Data snapshots are tracked in the database with metadata
- Refresh operations update both JSON files and database records
- This approach reduces API calls and improves performance

### Comparison Logic
- **CMS Blocks**: Matched by `identifier` field
- **CMS Pages**: Matched by `url_key` field
- Status types: MISSING, DIFFERENT, SAME
- Field-by-field comparison with detailed diff generation

### Sync Process
1. Preview phase - shows what will be changed
2. Execution phase - performs actual sync operations
3. Background processing for large sync operations
4. Automatic data refresh after successful sync

## Project Structure

```
cmssync/
├── backend/
│   ├── api/          # FastAPI route handlers
│   ├── models/       # SQLAlchemy models and schemas
│   ├── services/     # Business logic services
│   ├── integrations/ # Magento API client
│   ├── data/         # JSON file storage
│   └── main.py       # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable React components
│   │   ├── pages/      # Main application pages
│   │   ├── services/   # API client services
│   │   └── store/      # Zustand state management
│   └── package.json
└── start-dev.sh       # Quick start script
```

## API Endpoints

### Instance Management
- `GET /api/instances/` - List all instances
- `POST /api/instances/` - Create new instance
- `PUT /api/instances/{id}` - Update instance
- `DELETE /api/instances/{id}` - Delete instance
- `POST /api/instances/{id}/test` - Test connection
- `GET /api/instances/data-snapshots/all` - Get snapshot info for all instances

### Comparison
- `POST /api/compare/blocks` - Compare CMS blocks
- `POST /api/compare/pages` - Compare CMS pages  
- `POST /api/compare/refresh/{id}` - Refresh instance data

### Synchronization
- `POST /api/sync/preview` - Preview sync changes
- `POST /api/sync/execute` - Execute sync operation
- `GET /api/sync/status/{sync_id}` - Get sync status

### History
- `GET /api/history/` - Get sync history with filters
- `GET /api/history/statistics` - Get sync statistics
- `GET /api/history/{sync_id}` - Get detailed sync info

## Frontend Pages

### Instances Page
- Manage Magento 2 instances
- Test connections
- Refresh data with visual indicators
- Shows item counts and last update times

### Compare Page
- Select source and destination instances
- View comparison results in tables
- Filter by status (missing, different, same)
- Search by identifier or title
- Bulk selection for sync operations
- Expandable rows for details
- Diff viewer for field comparison

### Sync Page
- Monitor active sync operations
- Real-time progress updates
- Success/failure reporting

### History Page
- View all sync operations
- Filter by date, status, instances
- Export to CSV functionality

## Key Components

### DiffViewer
- Side-by-side comparison of fields
- Syntax highlighting for HTML content
- Visual indicators for changes

### SyncDialog
- Multi-step sync process
- Field selection
- Preview before execution
- Progress tracking

### InstanceFormModal
- Add/edit Magento instances
- Form validation
- Connection testing

## State Management

Using Zustand for global state:
- Selected instances
- Comparison results
- Selected items for sync
- Loading states
- Snackbar notifications

## Security Considerations

- API tokens stored in database (consider encryption)
- CORS configured for frontend access
- Input validation on all endpoints
- No direct file system access from frontend

## Development Commands

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
PORT=3001 npm start
```

### Quick Start
```bash
./start-dev.sh
```

## Testing Approach

- Unit tests for business logic
- Integration tests for API endpoints
- Playwright for E2E testing (planned)
- Manual testing checklist in tasklist.md

## Performance Optimizations

1. **JSON File Caching**: Data stored locally to reduce API calls
2. **Pagination**: All list endpoints support pagination
3. **Bulk Operations**: Sync multiple items in one operation
4. **Background Processing**: Large sync operations run asynchronously
5. **Optimized Queries**: Efficient database queries with proper indexing

## Known Limitations

1. No real-time sync between multiple users
2. Limited to REST API (no GraphQL support)
3. No automatic conflict resolution
4. English-only interface

## Future Enhancements

1. Add support for other Magento 2 content types
2. Implement webhooks for real-time updates
3. Add role-based access control
4. Support for multiple store views
5. Automated sync scheduling
6. Audit log with detailed change tracking