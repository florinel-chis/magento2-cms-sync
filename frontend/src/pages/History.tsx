import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import useStore from '../store';
import historyService from '../services/historyService';

interface SyncHistoryItem {
  id: number;
  source_instance_id: number;
  source_instance_name: string;
  destination_instance_id: number;
  destination_instance_name: string;
  sync_type: string;
  sync_status: string;
  items_synced: number;
  items_failed: number;
  started_at: string;
  completed_at: string | null;
  duration: number | null;
  error_message?: string | null;
}

export default function History() {
  const { instances, showSnackbar } = useStore();
  const [history, setHistory] = useState<SyncHistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<SyncHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedItem, setSelectedItem] = useState<SyncHistoryItem | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Filters
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterSource, setFilterSource] = useState<string>('all');
  const [filterDest, setFilterDest] = useState<string>('all');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      const response = await historyService.getHistory({
        skip: 0,
        limit: 100 // API maximum
      });
      setHistory(response.items);
      setFilteredHistory(response.items);
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to load history', 'error');
    } finally {
      setLoading(false);
    }
  }, [showSnackbar]);

  const applyFilters = useCallback(() => {
    let filtered = [...history];

    if (filterStatus !== 'all') {
      filtered = filtered.filter(item => item.sync_status === filterStatus);
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(item => item.sync_type === filterType);
    }

    if (filterSource !== 'all') {
      filtered = filtered.filter(item => item.source_instance_name === filterSource);
    }

    if (filterDest !== 'all') {
      filtered = filtered.filter(item => item.destination_instance_name === filterDest);
    }

    if (startDate) {
      filtered = filtered.filter(item => new Date(item.started_at) >= startDate);
    }

    if (endDate) {
      filtered = filtered.filter(item => new Date(item.started_at) <= endDate);
    }

    setFilteredHistory(filtered);
    setPage(0);
  }, [history, filterStatus, filterType, filterSource, filterDest, startDate, endDate]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const clearFilters = () => {
    setFilterStatus('all');
    setFilterType('all');
    setFilterSource('all');
    setFilterDest('all');
    setStartDate(null);
    setEndDate(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" fontSize="small" />;
      case 'failed':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'in_progress':
        return <CircularProgress size={16} />;
      case 'pending':
        return <WarningIcon color="warning" fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusChip = (status: string) => {
    const configs = {
      completed: { label: 'Completed', color: 'success' as const },
      failed: { label: 'Failed', color: 'error' as const },
      in_progress: { label: 'In Progress', color: 'primary' as const },
      pending: { label: 'Pending', color: 'warning' as const },
    };

    const config = configs[status as keyof typeof configs] || { label: status, color: 'default' as const };
    const icon = getStatusIcon(status);
    
    return (
      <Chip
        {...(icon && { icon })}
        label={config.label}
        color={config.color}
        size="small"
      />
    );
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const handleExport = () => {
    // Export filtered history to CSV
    const csv = [
      ['Date', 'Source', 'Destination', 'Type', 'Status', 'Items Synced', 'Items Failed', 'Duration'],
      ...filteredHistory.map(item => [
        new Date(item.started_at).toLocaleString(),
        item.source_instance_name,
        item.destination_instance_name,
        item.sync_type,
        item.sync_status,
        item.items_synced,
        item.items_failed,
        item.duration ? formatDuration(item.duration) : '-',
      ]),
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sync-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const paginatedHistory = useMemo(() => {
    return filteredHistory.slice(
      page * rowsPerPage,
      page * rowsPerPage + rowsPerPage
    );
  }, [filteredHistory, page, rowsPerPage]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Sync History</Typography>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={filteredHistory.length === 0}
          >
            Export CSV
          </Button>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <FilterIcon />
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                label="Type"
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="blocks">Blocks</MenuItem>
                <MenuItem value="pages">Pages</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Source</InputLabel>
              <Select
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                label="Source"
              >
                <MenuItem value="all">All</MenuItem>
                {Array.from(new Set(history.map(item => item.source_instance_name))).map(name => (
                  <MenuItem key={name} value={name}>{name}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Destination</InputLabel>
              <Select
                value={filterDest}
                onChange={(e) => setFilterDest(e.target.value)}
                label="Destination"
              >
                <MenuItem value="all">All</MenuItem>
                {Array.from(new Set(history.map(item => item.destination_instance_name))).map(name => (
                  <MenuItem key={name} value={name}>{name}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={setStartDate}
              slotProps={{
                textField: { size: 'small' }
              }}
            />

            <DatePicker
              label="End Date"
              value={endDate}
              onChange={setEndDate}
              slotProps={{
                textField: { size: 'small' }
              }}
            />

            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
            >
              Clear Filters
            </Button>
          </Stack>
        </Paper>

        {/* History Table */}
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Source → Destination</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Items</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedHistory.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary" py={3}>
                        No sync history found for the selected filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedHistory.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        {new Date(item.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {item.source_instance_name} → {item.destination_instance_name}
                      </TableCell>
                      <TableCell>
                        <Chip label={item.sync_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{getStatusChip(item.sync_status)}</TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color="success.main">
                          {item.items_synced}
                        </Typography>
                        {item.items_failed > 0 && (
                          <Typography variant="body2" color="error.main">
                            {item.items_failed} failed
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{item.duration ? formatDuration(item.duration) : '-'}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedItem(item);
                              setDetailsOpen(true);
                            }}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={filteredHistory.length}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[10, 25, 50, 100]}
          />
        </Paper>

        {/* Details Dialog */}
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Sync Details</DialogTitle>
          <DialogContent>
            {selectedItem && (
              <List>
                <ListItem>
                  <ListItemText
                    primary="Sync ID"
                    secondary={selectedItem.id}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Started"
                    secondary={new Date(selectedItem.started_at).toLocaleString()}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Completed"
                    secondary={selectedItem.completed_at ? new Date(selectedItem.completed_at).toLocaleString() : 'Not completed'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Total Items Processed"
                    secondary={selectedItem.items_synced + selectedItem.items_failed}
                  />
                </ListItem>
                {selectedItem.error_message && (
                  <ListItem>
                    <ListItemText
                      primary="Error Message"
                      secondary={selectedItem.error_message}
                    />
                  </ListItem>
                )}
              </List>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
}