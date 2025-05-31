import React, { useState, useEffect } from 'react';
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
  Checkbox,
  FormControlLabel,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Sync as SyncIcon,
  Preview as PreviewIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Add as AddIcon,
  Update as UpdateIcon,
} from '@mui/icons-material';
import syncService from '../services/syncService';
import { DataType, SyncItem, SyncPreview, SyncResult } from '../types';
import useStore from '../store';

interface SyncDialogProps {
  open: boolean;
  onClose: () => void;
  sourceInstanceId: number;
  destinationInstanceId: number;
  dataType: DataType;
  items: Array<{
    identifier: string;
    title: string;
    action: 'create' | 'update';
  }>;
}

export default function SyncDialog({
  open,
  onClose,
  sourceInstanceId,
  destinationInstanceId,
  dataType,
  items,
}: SyncDialogProps) {
  const { showSnackbar } = useStore();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<SyncPreview | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [selectedItems, setSelectedItems] = useState<string[]>(items.map(i => i.identifier));
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(0);

  const steps = ['Select Items', 'Preview Changes', 'Execute Sync'];

  useEffect(() => {
    if (open) {
      setActiveStep(0);
      setSelectedItems(items.map(i => i.identifier));
      setSyncResult(null);
      setPreview(null);
    }
  }, [open, items]);

  const handlePreview = async () => {
    try {
      setLoading(true);
      
      const syncItems: SyncItem[] = items
        .filter(item => selectedItems.includes(item.identifier))
        .map(item => ({
          identifier: item.identifier,
          action: item.action,
        }));

      const previewResult = await syncService.previewSync({
        source_instance_id: sourceInstanceId,
        destination_instance_id: destinationInstanceId,
        data_type: dataType,
        items: syncItems,
      });

      setPreview(previewResult);
      setActiveStep(1);
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to generate preview', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncProgress(0);
      
      const syncItems: SyncItem[] = items
        .filter(item => selectedItems.includes(item.identifier))
        .map(item => ({
          identifier: item.identifier,
          action: item.action,
        }));

      const result = dataType === DataType.BLOCKS
        ? await syncService.syncBlocks({
            source_instance_id: sourceInstanceId,
            destination_instance_id: destinationInstanceId,
            data_type: dataType,
            items: syncItems,
          })
        : await syncService.syncPages({
            source_instance_id: sourceInstanceId,
            destination_instance_id: destinationInstanceId,
            data_type: dataType,
            items: syncItems,
          });

      setSyncResult(result);
      setActiveStep(2);

      // Poll for sync status
      if (result.status === 'pending' || result.status === 'in_progress') {
        pollSyncStatus(result.sync_id);
      }
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to start sync', 'error');
    } finally {
      setSyncing(false);
    }
  };

  const pollSyncStatus = async (syncId: number) => {
    const poll = async () => {
      try {
        const status = await syncService.getSyncStatus(syncId);
        setSyncResult(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          setSyncProgress(100);
          showSnackbar(
            status.status === 'completed'
              ? `Sync completed: ${status.items_synced} succeeded, ${status.items_failed} failed`
              : 'Sync failed',
            status.status === 'completed' ? 'success' : 'error'
          );
          return;
        }

        // Calculate progress
        const total = status.items_synced + status.items_failed;
        const progress = total > 0 ? (total / selectedItems.length) * 100 : 0;
        setSyncProgress(progress);

        // Continue polling
        setTimeout(poll, 2000);
      } catch (error) {
        console.error('Failed to poll sync status:', error);
      }
    };

    poll();
  };

  const handleToggleItem = (identifier: string) => {
    setSelectedItems(prev =>
      prev.includes(identifier)
        ? prev.filter(id => id !== identifier)
        : [...prev, identifier]
    );
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <>
            <Typography variant="body2" gutterBottom>
              Select items to sync:
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedItems.length === items.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems(items.map(i => i.identifier));
                          } else {
                            setSelectedItems([]);
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>Identifier</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((item) => (
                    <TableRow key={item.identifier}>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedItems.includes(item.identifier)}
                          onChange={() => handleToggleItem(item.identifier)}
                        />
                      </TableCell>
                      <TableCell>{item.identifier}</TableCell>
                      <TableCell>{item.title}</TableCell>
                      <TableCell>
                        <Chip
                          icon={item.action === 'create' ? <AddIcon /> : <UpdateIcon />}
                          label={item.action}
                          size="small"
                          color={item.action === 'create' ? 'success' : 'primary'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );

      case 1:
        return preview ? (
          <>
            <Alert severity="info" sx={{ mb: 2 }}>
              Preview of changes to be made:
            </Alert>
            <Box mb={2}>
              <Typography variant="body2">
                Total changes: {preview.total_changes}
              </Typography>
              <Typography variant="body2" color="success.main">
                Creates: {preview.creates}
              </Typography>
              <Typography variant="body2" color="primary.main">
                Updates: {preview.updates}
              </Typography>
            </Box>
          </>
        ) : (
          <CircularProgress />
        );

      case 2:
        return syncResult ? (
          <>
            {syncResult.status === 'in_progress' && (
              <>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Sync in progress...
                </Alert>
                <LinearProgress variant="determinate" value={syncProgress} sx={{ mb: 2 }} />
              </>
            )}
            
            {syncResult.status === 'completed' && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Sync completed successfully!
              </Alert>
            )}
            
            {syncResult.status === 'failed' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Sync failed: {syncResult.error_message}
              </Alert>
            )}

            <Box mb={2}>
              <Typography variant="body2" color="success.main">
                Successfully synced: {syncResult.items_synced}
              </Typography>
              <Typography variant="body2" color="error.main">
                Failed: {syncResult.items_failed}
              </Typography>
            </Box>

            {syncResult.details && syncResult.details.length > 0 && (
              <List dense>
                {syncResult.details.map((detail, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {detail.success ? (
                        <CheckIcon color="success" />
                      ) : (
                        <ErrorIcon color="error" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={detail.identifier}
                      secondary={detail.message || detail.error}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </>
        ) : (
          <CircularProgress />
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SyncIcon />
          <Typography variant="h6">
            Sync {dataType === DataType.BLOCKS ? 'CMS Blocks' : 'CMS Pages'}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent()}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        
        {activeStep === 0 && (
          <Button
            variant="contained"
            onClick={handlePreview}
            disabled={selectedItems.length === 0 || loading}
            startIcon={loading ? <CircularProgress size={20} /> : <PreviewIcon />}
          >
            Preview
          </Button>
        )}
        
        {activeStep === 1 && preview && (
          <>
            <Button onClick={() => setActiveStep(0)}>Back</Button>
            <Button
              variant="contained"
              onClick={handleSync}
              disabled={syncing}
              startIcon={syncing ? <CircularProgress size={20} /> : <SyncIcon />}
            >
              Execute Sync
            </Button>
          </>
        )}
        
        {activeStep === 2 && syncResult?.status === 'completed' && (
          <Button variant="contained" onClick={onClose}>
            Done
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}