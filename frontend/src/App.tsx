import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import Layout from './components/Layout';
import NotificationSnackbar from './components/NotificationSnackbar';
import ErrorBoundary from './components/ErrorBoundary';
import Instances from './pages/Instances';
import Compare from './pages/Compare';
import CompareBlocks from './pages/CompareBlocks';
import ComparePages from './pages/ComparePages';
import Sync from './pages/Sync';
import History from './pages/History';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
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
        </Router>
        <NotificationSnackbar />
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
