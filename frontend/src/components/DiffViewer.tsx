import React, { useState, useEffect, useCallback, memo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  Tabs,
  Tab,
} from '@mui/material';
import { 
  CompareArrows as CompareIcon,
  Close as CloseIcon,
  TableChart as TableIcon,
  ViewColumn as SplitIcon,
  ViewStream as UnifiedIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import comparisonService from '../services/comparisonService';
import syncService from '../services/syncService';
import { DiffResult, DataType, DiffField, SyncItem } from '../types';
import DiffDisplay from './DiffDisplay';
import useStore from '../store';

interface DiffViewerProps {
  open: boolean;
  onClose: () => void;
  sourceInstanceId: number;
  destinationInstanceId: number;
  dataType: DataType;
  identifier: string;
  title: string;
}

function DiffViewer({
  open,
  onClose,
  sourceInstanceId,
  destinationInstanceId,
  dataType,
  identifier,
  title,
}: DiffViewerProps) {
  const { showSnackbar } = useStore();
  const [loading, setLoading] = useState(false);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'split' | 'unified'>('table');
  const [syncing, setSyncing] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);

  const loadDiff = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await comparisonService.getItemDiff({
        source_instance_id: sourceInstanceId,
        destination_instance_id: destinationInstanceId,
        data_type: dataType,
        identifier: identifier,
      });


      // Compute additional properties
      const hasDifferences = result.fields.some(field => field.is_different);
      const destinationExists = result.destination_stores.length > 0 ||
                               result.fields.some(field => field.destination_value !== null && field.destination_value !== undefined);


      setDiffResult({
        ...result,
        has_differences: hasDifferences,
        destination_exists: destinationExists
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load diff');
    } finally {
      setLoading(false);
    }
  }, [sourceInstanceId, destinationInstanceId, dataType, identifier]);

  useEffect(() => {
    if (open) {
      loadDiff();
    }
  }, [open, loadDiff]);

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) {
      return '(empty)';
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const handleSync = useCallback(async () => {
    if (!diffResult) return;

    setConfirmDialogOpen(false);


    try {
      setSyncing(true);

      // Determine if this is a create or update operation
      const action = diffResult.destination_exists ? 'update' : 'create';

      const syncItem: SyncItem = {
        identifier: identifier,
        action: action as 'create' | 'update',
      };

      // Execute sync based on data type
      const syncRequest = {
        source_instance_id: sourceInstanceId,
        destination_instance_id: destinationInstanceId,
        data_type: dataType,
        items: [syncItem],
      };


      const result = dataType === DataType.BLOCKS
        ? await syncService.syncBlocks(syncRequest)
        : await syncService.syncPages(syncRequest);


      if (result.status === 'completed' || result.status === 'pending') {
        showSnackbar(`Successfully synced ${title || identifier}`, 'success');

        // Reload the diff to show updated state
        await loadDiff();
      } else {
        showSnackbar(`Failed to sync: ${result.error_message || 'Unknown error'}`, 'error');
      }
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to sync item', 'error');
    } finally {
      setSyncing(false);
    }
  }, [diffResult, identifier, sourceInstanceId, destinationInstanceId, dataType, showSnackbar, title, loadDiff]);

  const renderFieldDiff = (field: DiffField) => {
    if (!field.is_different) {
      return null;
    }

    const sourceValue = formatValue(field.source_value);
    const destValue = formatValue(field.destination_value);

    // For non-table views, use DiffDisplay for content fields
    if (viewMode !== 'table' && (field.field_name === 'content' || sourceValue.length > 100 || destValue.length > 100)) {
      return (
        <Box key={field.field_name} mb={3}>
          <DiffDisplay
            oldValue={sourceValue}
            newValue={destValue}
            title={field.field_name}
            splitView={viewMode === 'split'}
          />
        </Box>
      );
    }

    // Table view for simple fields
    return (
      <TableRow key={field.field_name}>
        <TableCell component="th" scope="row">
          {field.field_name}
        </TableCell>
        <TableCell>
          <Box
            component="pre"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '0.875rem',
              m: 0,
              maxWidth: 400,
            }}
          >
            {sourceValue}
          </Box>
        </TableCell>
        <TableCell>
          <Box
            component="pre"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '0.875rem',
              m: 0,
              maxWidth: 400,
            }}
          >
            {destValue}
          </Box>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <CompareIcon />
            <Typography variant="h6">Diff: {title || identifier}</Typography>
          </Box>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="table">
              <TableIcon sx={{ mr: 0.5 }} fontSize="small" />
              Table
            </ToggleButton>
            <ToggleButton value="split">
              <SplitIcon sx={{ mr: 0.5 }} fontSize="small" />
              Split
            </ToggleButton>
            <ToggleButton value="unified">
              <UnifiedIcon sx={{ mr: 0.5 }} fontSize="small" />
              Unified
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : diffResult ? (
          <>
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Comparing: {identifier}
                  </Typography>
                  {diffResult.source_stores.length > 0 && (
                    <Box display="flex" gap={1} alignItems="center" mb={1}>
                      <Typography variant="caption">Source stores:</Typography>
                      {diffResult.source_stores.map(store => (
                        <Chip key={store} label={store} size="small" />
                      ))}
                    </Box>
                  )}
                  {diffResult.destination_stores.length > 0 && (
                    <Box display="flex" gap={1} alignItems="center">
                      <Typography variant="caption">Destination stores:</Typography>
                      {diffResult.destination_stores.map(store => (
                        <Chip key={store} label={store} size="small" />
                      ))}
                    </Box>
                  )}
                </Box>
                <Box textAlign="right">
                  {diffResult.has_differences ? (
                    <Alert severity="warning" sx={{ py: 0.5, px: 2 }}>
                      <Typography variant="caption">
                        {diffResult.destination_exists 
                          ? 'Item exists with differences' 
                          : 'Item missing in destination'}
                      </Typography>
                    </Alert>
                  ) : (
                    <Alert severity="success" sx={{ py: 0.5, px: 2 }}>
                      <Typography variant="caption">Items are identical</Typography>
                    </Alert>
                  )}
                </Box>
              </Box>
            </Box>

            {/* Group fields by type for better organization */}
            {(() => {
              const contentFields = diffResult.fields.filter(
                field => field.is_different && (field.field_name === 'content' || field.field_name === 'content_heading')
              );
              const metadataFields = diffResult.fields.filter(
                field => field.is_different && !['content', 'content_heading'].includes(field.field_name)
              );

              if (viewMode === 'table') {
                return (
                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Field</TableCell>
                          <TableCell>Source Value</TableCell>
                          <TableCell>Destination Value</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {diffResult.fields
                          .filter(field => field.is_different)
                          .map(renderFieldDiff)}
                      </TableBody>
                    </Table>
                  </TableContainer>
                );
              }

              return (
                <Box>
                  {/* Content fields with visual diff */}
                  {contentFields.length > 0 && (
                    <Box mb={3}>
                      <Typography variant="h6" gutterBottom>
                        Content Changes
                      </Typography>
                      {contentFields.map(field => (
                        <DiffDisplay
                          key={field.field_name}
                          oldValue={formatValue(field.source_value)}
                          newValue={formatValue(field.destination_value)}
                          title={field.field_name}
                          splitView={viewMode === 'split'}
                        />
                      ))}
                    </Box>
                  )}
                  
                  {/* Metadata fields in a table */}
                  {metadataFields.length > 0 && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Metadata Changes
                      </Typography>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Field</TableCell>
                              <TableCell>Source</TableCell>
                              <TableCell>Destination</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {metadataFields.map(renderFieldDiff)}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}
                </Box>
              );
            })()}
          </>
        ) : null}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} startIcon={<CloseIcon />}>
          Close
        </Button>
        {diffResult && diffResult.has_differences && (
          <Button 
            onClick={() => setConfirmDialogOpen(true)} 
            startIcon={syncing ? <CircularProgress size={20} /> : <SyncIcon />}
            variant="contained"
            color="primary"
            disabled={syncing || loading}
          >
            {syncing ? 'Syncing...' : `Push to Destination`}
          </Button>
        )}
      </DialogActions>
      
      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Sync</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will overwrite the content in the destination instance.
          </Alert>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to sync <strong>{title || identifier}</strong> from source to destination?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {diffResult?.destination_exists 
              ? 'The existing item in the destination will be updated with content from the source.'
              : 'A new item will be created in the destination with content from the source.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSync} 
            variant="contained" 
            color="primary"
            startIcon={<SyncIcon />}
          >
            Confirm Sync
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}

export default memo(DiffViewer);