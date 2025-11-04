import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Collapse,
  TablePagination,
  Tooltip,
  Stack,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Compare as CompareIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Sync as SyncIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import useStore from '../store';
import comparisonService from '../services/comparisonService';
import { DataType, ComparisonStatus, ComparisonItem } from '../types';
import DiffViewer from '../components/DiffViewer';
import SyncDialog from '../components/SyncDialog';

export default function ComparePages() {
  const {
    instances,
    selectedSourceInstance,
    selectedDestInstance,
    comparisonResult,
    loadingComparison,
    selectedItems,
    setSelectedSourceInstance,
    setSelectedDestInstance,
    setComparisonResult,
    setLoadingComparison,
    toggleItemSelection,
    selectAllItems,
    clearSelectedItems,
    showSnackbar,
  } = useStore();

  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [diffViewerOpen, setDiffViewerOpen] = useState(false);
  const [diffViewerItem, setDiffViewerItem] = useState<ComparisonItem | null>(null);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadInstances = useCallback(async () => {
    try {
      const response = await fetch('/api/instances/');
      const data = await response.json();
      useStore.getState().setInstances(data);
    } catch (error) {
      console.error('Failed to load instances:', error);
    }
  }, []);

  const handleCompare = useCallback(async () => {
    if (!selectedSourceInstance || !selectedDestInstance) {
      showSnackbar('Please select both source and destination instances', 'warning');
      return;
    }

    try {
      setLoadingComparison(true);

      const request = {
        source_instance_id: selectedSourceInstance.id,
        destination_instance_id: selectedDestInstance.id,
        force_refresh: false,
      };

      const result = await comparisonService.comparePages(request);
      setComparisonResult(result);
      showSnackbar('Comparison completed successfully', 'success');
    } catch (error: any) {
      showSnackbar(error.message || 'Comparison failed', 'error');
    } finally {
      setLoadingComparison(false);
    }
  }, [selectedSourceInstance, selectedDestInstance, showSnackbar, setLoadingComparison, setComparisonResult]);

  useEffect(() => {
    // Load instances if not already loaded
    if (instances.length === 0) {
      loadInstances();
    }
  }, [instances.length, loadInstances]);

  useEffect(() => {
    // Clear comparison when instances change
    if (selectedSourceInstance || selectedDestInstance) {
      setComparisonResult(null);
      clearSelectedItems();
    }
  }, [selectedSourceInstance, selectedDestInstance, setComparisonResult, clearSelectedItems]);

  const handleToggleRow = (identifier: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(identifier)) {
      newExpanded.delete(identifier);
    } else {
      newExpanded.add(identifier);
    }
    setExpandedRows(newExpanded);
  };

  const handleViewDiff = (item: ComparisonItem) => {
    setDiffViewerItem(item);
    setDiffViewerOpen(true);
  };

  const handleOpenSync = () => {
    if (!comparisonResult || selectedItems.length === 0) return;
    setSyncDialogOpen(true);
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked && comparisonResult) {
      const allIdentifiers = comparisonResult.items
        .filter(item => 
          item.source_status !== ComparisonStatus.MISSING &&
          (item.source_status === ComparisonStatus.DIFFERENT || 
           item.destination_status === ComparisonStatus.MISSING)
        )
        .map(item => item.identifier);
      selectAllItems(allIdentifiers);
    } else {
      clearSelectedItems();
    }
  };

  const getStatusChip = (item: ComparisonItem) => {
    if (item.source_status === ComparisonStatus.MISSING) {
      return <Chip label="Only in Destination" color="warning" size="small" />;
    }
    if (item.destination_status === ComparisonStatus.MISSING) {
      return <Chip label="Missing in Destination" color="error" size="small" />;
    }
    if (item.source_status === ComparisonStatus.DIFFERENT) {
      return <Chip label="Different" color="info" size="small" />;
    }
    return <Chip label="Same" color="success" size="small" />;
  };

  const filteredItems = useMemo(() => {
    return comparisonResult?.items.filter(item => {
      // Apply status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'missing' && item.destination_status !== ComparisonStatus.MISSING) {
          return false;
        }
        if (statusFilter === 'different' && item.source_status !== ComparisonStatus.DIFFERENT) {
          return false;
        }
        if (statusFilter === 'same' && (item.source_status === ComparisonStatus.DIFFERENT || item.destination_status === ComparisonStatus.MISSING || item.source_status === ComparisonStatus.MISSING)) {
          return false;
        }
      }

      // Apply search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return item.identifier.toLowerCase().includes(query) ||
               item.source_data?.title?.toLowerCase().includes(query) ||
               item.destination_data?.title?.toLowerCase().includes(query);
      }

      return true;
    }) || [];
  }, [comparisonResult, statusFilter, searchQuery]);

  const paginatedItems = useMemo(() => {
    return filteredItems.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [filteredItems, page, rowsPerPage]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Compare CMS Pages
      </Typography>

      {/* Instance Selection */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="flex-end">
          <FormControl fullWidth>
            <InputLabel>Source Instance</InputLabel>
            <Select
              value={selectedSourceInstance?.id || ''}
              onChange={(e) => {
                const instance = instances.find(i => i.id === e.target.value);
                setSelectedSourceInstance(instance || null);
              }}
              label="Source Instance"
            >
              <MenuItem value="">
                <em>Select source instance</em>
              </MenuItem>
              {instances.map((instance) => (
                <MenuItem key={instance.id} value={instance.id}>
                  {instance.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Destination Instance</InputLabel>
            <Select
              value={selectedDestInstance?.id || ''}
              onChange={(e) => {
                const instance = instances.find(i => i.id === e.target.value);
                setSelectedDestInstance(instance || null);
              }}
              label="Destination Instance"
            >
              <MenuItem value="">
                <em>Select destination instance</em>
              </MenuItem>
              {instances.map((instance) => (
                <MenuItem key={instance.id} value={instance.id}>
                  {instance.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            startIcon={<CompareIcon />}
            onClick={handleCompare}
            disabled={!selectedSourceInstance || !selectedDestInstance || loadingComparison}
          >
            Compare
          </Button>
        </Stack>

        {selectedSourceInstance && selectedDestInstance && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Comparing pages from <strong>{selectedSourceInstance.name}</strong> to{' '}
            <strong>{selectedDestInstance.name}</strong>
          </Alert>
        )}
      </Paper>

      <Paper>
        {loadingComparison ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : comparisonResult ? (
          <>
            <Box p={2}>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Total: {comparisonResult.total_source} in source, {comparisonResult.total_destination} in destination
                </Typography>
                <Chip label={`${comparisonResult.exists_in_both} Same`} color="success" size="small" />
                <Chip label={`${comparisonResult.different} Different`} color="info" size="small" />
                <Chip label={`${comparisonResult.missing_in_destination} Missing`} color="error" size="small" />
                {selectedItems.length > 0 && (
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    startIcon={<SyncIcon />}
                    onClick={handleOpenSync}
                  >
                    Sync {selectedItems.length} items
                  </Button>
                )}
              </Stack>
              
              <Stack direction="row" spacing={2} alignItems="center">
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Status Filter</InputLabel>
                  <Select
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setPage(0);
                    }}
                    label="Status Filter"
                  >
                    <MenuItem value="all">All Items</MenuItem>
                    <MenuItem value="missing">Missing</MenuItem>
                    <MenuItem value="different">Different</MenuItem>
                    <MenuItem value="same">Same</MenuItem>
                  </Select>
                </FormControl>
                
                <TextField
                  size="small"
                  placeholder="Search by identifier or title..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(0);
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ minWidth: 300 }}
                />
                
                <Typography variant="body2" color="text.secondary">
                  Showing {filteredItems.length} of {comparisonResult.items.length} items
                </Typography>
              </Stack>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        onChange={handleSelectAll}
                        checked={selectedItems.length > 0 && selectedItems.length === filteredItems.filter(item => 
                          item.source_status !== ComparisonStatus.MISSING &&
                          (item.source_status === ComparisonStatus.DIFFERENT || 
                           item.destination_status === ComparisonStatus.MISSING)
                        ).length}
                      />
                    </TableCell>
                    <TableCell>Identifier</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedItems.map((item) => (
                    <React.Fragment key={item.identifier}>
                      <TableRow>
                        <TableCell padding="checkbox">
                          {item.source_status !== ComparisonStatus.MISSING && (
                            item.source_status === ComparisonStatus.DIFFERENT || 
                            item.destination_status === ComparisonStatus.MISSING
                          ) && (
                            <Checkbox
                              checked={selectedItems.includes(item.identifier)}
                              onChange={() => toggleItemSelection(item.identifier)}
                            />
                          )}
                        </TableCell>
                        <TableCell>{item.identifier}</TableCell>
                        <TableCell>{item.title}</TableCell>
                        <TableCell>{getStatusChip(item)}</TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleToggleRow(item.identifier)}
                            >
                              {expandedRows.has(item.identifier) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          </Tooltip>
                          {item.source_status === ComparisonStatus.DIFFERENT && (
                            <Tooltip title="View Diff">
                              <IconButton
                                size="small"
                                onClick={() => handleViewDiff(item)}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                          <Collapse in={expandedRows.has(item.identifier)} timeout="auto" unmountOnExit>
                            <Box sx={{ margin: 1 }}>
                              <Typography variant="h6" gutterBottom component="div">
                                Details
                              </Typography>
                              <Table size="small">
                                <TableBody>
                                  {item.source_data && (
                                    <>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Store Views (Source)</TableCell>
                                        <TableCell>{item.source_data.store_id?.join(', ') || 'All'}</TableCell>
                                      </TableRow>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Active (Source)</TableCell>
                                        <TableCell>{item.source_data.active === '1' ? 'Yes' : 'No'}</TableCell>
                                      </TableRow>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Page Layout (Source)</TableCell>
                                        <TableCell>{item.source_data.page_layout || 'Default'}</TableCell>
                                      </TableRow>
                                    </>
                                  )}
                                  {item.destination_data && (
                                    <>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Store Views (Destination)</TableCell>
                                        <TableCell>{item.destination_data.store_id?.join(', ') || 'All'}</TableCell>
                                      </TableRow>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Active (Destination)</TableCell>
                                        <TableCell>{item.destination_data.active === '1' ? 'Yes' : 'No'}</TableCell>
                                      </TableRow>
                                      <TableRow>
                                        <TableCell component="th" scope="row">Page Layout (Destination)</TableCell>
                                        <TableCell>{item.destination_data.page_layout || 'Default'}</TableCell>
                                      </TableRow>
                                    </>
                                  )}
                                  {item.differences && (
                                    <TableRow>
                                      <TableCell component="th" scope="row">Differences</TableCell>
                                      <TableCell>{item.differences.join(', ')}</TableCell>
                                    </TableRow>
                                  )}
                                </TableBody>
                              </Table>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={filteredItems.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
            />
          </>
        ) : (
          <Box p={4} textAlign="center">
            <Typography variant="body1" color="text.secondary">
              Select source and destination instances and click "Compare" to see the differences
            </Typography>
          </Box>
        )}
      </Paper>

      {diffViewerItem && (
        <DiffViewer
          open={diffViewerOpen}
          onClose={() => setDiffViewerOpen(false)}
          sourceInstanceId={selectedSourceInstance?.id || 0}
          destinationInstanceId={selectedDestInstance?.id || 0}
          dataType={DataType.PAGES}
          identifier={diffViewerItem.identifier}
          title={diffViewerItem.title}
        />
      )}

      {syncDialogOpen && comparisonResult && (
        <SyncDialog
          open={syncDialogOpen}
          onClose={() => setSyncDialogOpen(false)}
          sourceInstanceId={selectedSourceInstance!.id}
          destinationInstanceId={selectedDestInstance!.id}
          dataType={DataType.PAGES}
          items={comparisonResult.items
            .filter(item => selectedItems.includes(item.identifier))
            .map(item => ({
              identifier: item.identifier,
              title: item.title,
              action: item.destination_status === ComparisonStatus.MISSING ? 'create' : 'update' as 'create' | 'update'
            }))}
        />
      )}
    </Box>
  );
}