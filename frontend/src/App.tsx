import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { Box, CircularProgress } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import Layout from './components/Layout';
import NotificationSnackbar from './components/NotificationSnackbar';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load all page components for better performance
const Instances = lazy(() => import('./pages/Instances'));
const Compare = lazy(() => import('./pages/Compare'));
const CompareBlocks = lazy(() => import('./pages/CompareBlocks'));
const ComparePages = lazy(() => import('./pages/ComparePages'));
const Sync = lazy(() => import('./pages/Sync'));
const History = lazy(() => import('./pages/History'));

// Loading fallback component
function LoadingFallback() {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="400px"
    >
      <CircularProgress />
    </Box>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Navigate to="/instances" replace />} />
                <Route path="instances" element={<Instances />} />
                <Route path="compare" element={<Compare />} />
                <Route path="compare-blocks" element={<CompareBlocks />} />
                <Route path="compare-pages" element={<ComparePages />} />
                <Route path="sync" element={<Sync />} />
                <Route path="history" element={<History />} />
              </Route>
            </Routes>
          </Suspense>
        </Router>
        <NotificationSnackbar />
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
