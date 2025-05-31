# Magento CMS Sync - Frontend

This is the React frontend for the Magento CMS Sync application.

## Overview

The frontend provides a user interface for:
- Managing Magento instances
- Comparing CMS content (pages and blocks) between instances
- Synchronizing content from source to destination instances
- Viewing sync history

## Development

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation

```bash
npm install
```

### Running in Development

```bash
npm start
```

The app will run on [http://localhost:3000](http://localhost:3000) and proxy API requests to the backend on port 8000.

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Technology Stack

- React 19 with TypeScript
- Material-UI (MUI) for UI components
- React Router for navigation
- Axios for API calls
- Zustand for state management
- Diff library for content comparison visualization

## Project Structure

- `/src/components` - Reusable UI components
- `/src/pages` - Page components for different routes
- `/src/services` - API service layers
- `/src/store` - Zustand store for global state
- `/src/types` - TypeScript type definitions
- `/src/utils` - Utility functions