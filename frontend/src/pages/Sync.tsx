import React, { useState, useEffect, useCallback } from 'react';
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
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  PlayArrow as InProgressIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import syncService from '../services/syncService';
import historyService from '../services/historyService';
import useStore from '../store';

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

interface SyncStatistics {
  period: string;
  total_syncs: number;
  completed_syncs: number;
  failed_syncs: number;
  active_syncs: number;
  success_rate: number;
  total_items_synced: number;
  total_items_failed: number;
  active_sync_details: Array<{
    id: number;
    sync_type: string;
    status: string;
    progress: number;
  }>;
}

export default function Sync() {
  const navigate = useNavigate();
  const { showSnackbar, instances } = useStore();
  const [activeSyncs, setActiveSyncs] = useState<SyncHistoryItem[]>([]);
  const [recentSyncs, setRecentSyncs] = useState<SyncHistoryItem[]>([]);
  const [statistics, setStatistics] = useState<SyncStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSync, setSelectedSync] = useState<number | null>(null);
  const [syncDetails, setSyncDetails] = useState<any>(null);

  const loadSyncData = useCallback(async () => {
    try {
      setLoading(true);

      // Load statistics
      const statsResponse = await historyService.getStatistics('today');
      setStatistics(statsResponse);

      // Load active syncs (pending or in_progress)
      const allSyncsResponse = await historyService.getHistory({
        skip: 0,
        limit: 50
      });

      // Filter active syncs on the client side
      const activeSyncsFiltered = allSyncsResponse.items.filter(
        (item: SyncHistoryItem) => item.sync_status === 'pending' || item.sync_status === 'in_progress'
      ).sort((a: SyncHistoryItem, b: SyncHistoryItem) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());

      setActiveSyncs(activeSyncsFiltered);

      // Load recent completed syncs (use the same response to avoid another API call)
      const completedSyncs = allSyncsResponse.items.filter(
        (item: SyncHistoryItem) => item.sync_status === 'completed' || item.sync_status === 'failed'
      ).slice(0, 5);

      setRecentSyncs(completedSyncs);

    } catch (error: any) {
      console.error('Failed to load sync data:', error);
      showSnackbar(error.message || 'Failed to load sync data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showSnackbar]);

  const loadSyncDetails = useCallback(async (syncId: number) => {
    try {
      const details = await historyService.getSyncDetails(syncId);
      setSyncDetails(details);
      setSelectedSync(syncId);
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to load sync details', 'error');
    }
  }, [showSnackbar]);

  useEffect(() => {
    loadSyncData();
    // Poll for updates every 5 seconds
    const interval = setInterval(loadSyncData, 5000);
    return () => clearInterval(interval);
  }, [loadSyncData]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <InProgressIcon color="primary" />;
      case 'pending':
        return <PendingIcon color="warning" />;
      default:
        return null;
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig = {
      completed: { label: 'Completed', color: 'success' as const },
      failed: { label: 'Failed', color: 'error' as const },
      in_progress: { label: 'In Progress', color: 'primary' as const },
      pending: { label: 'Pending', color: 'warning' as const },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || {
      label: status,
      color: 'default' as const,
    };

    return <Chip label={config.label} color={config.color} size="small" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Sync Operations</Typography>
        <Button
          variant="contained"
          startIcon={<SyncIcon />}
          onClick={() => navigate('/compare')}
        >
          New Sync
        </Button>
      </Box>

      {/* Active Syncs */}
      {activeSyncs.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Box p={2}>
            <Typography variant="h6" gutterBottom>
              Active Syncs
            </Typography>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Source → Destination</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {activeSyncs.map((sync) => {
                  const totalItems = sync.items_synced + sync.items_failed;
                  const progressPercent = totalItems > 0 ? (sync.items_synced / totalItems) * 100 : 0;
                  
                  return (
                    <TableRow key={sync.id}>
                      <TableCell>
                        {sync.source_instance_name} → {sync.destination_instance_name}
                      </TableCell>
                      <TableCell>
                        <Chip label={sync.sync_type} size="small" />
                      </TableCell>
                      <TableCell>{getStatusChip(sync.sync_status)}</TableCell>
                      <TableCell sx={{ minWidth: 200 }}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Box width="100%">
                            <LinearProgress
                              variant={sync.sync_status === 'pending' ? 'indeterminate' : 'determinate'}
                              value={progressPercent}
                            />
                          </Box>
                          <Typography variant="caption">
                            {sync.items_synced}/{totalItems || '?'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {new Date(sync.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => loadSyncDetails(sync.id)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* No Active Syncs Message */}
      {activeSyncs.length === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No active sync operations. Start a new sync from the Compare page.
        </Alert>
      )}

      {/* Sync Statistics */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(25% - 24px)' } }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Syncs Today
              </Typography>
              <Typography variant="h4">{statistics?.total_syncs || 0}</Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(25% - 24px)' } }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4" color="success.main">
                {statistics?.success_rate || 0}%
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(25% - 24px)' } }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Items Synced
              </Typography>
              <Typography variant="h4">{statistics?.total_items_synced || 0}</Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(25% - 24px)' } }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Failed Items
              </Typography>
              <Typography variant="h4" color="error.main">
                {statistics?.total_items_failed || 0}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Recent Syncs */}
      <Paper>
        <Box p={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Recent Syncs</Typography>
          <IconButton onClick={loadSyncData}>
            <RefreshIcon />
          </IconButton>
        </Box>
        {recentSyncs.length === 0 ? (
          <Box p={4} textAlign="center">
            <Typography variant="body1" color="text.secondary">
              No sync history available yet.
            </Typography>
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Source → Destination</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Items</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Completed</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentSyncs.map((sync) => {
                  const formatDuration = (duration: number | null) => {
                    if (!duration) return '-';
                    if (duration < 60) return `${duration}s`;
                    const minutes = Math.floor(duration / 60);
                    const seconds = duration % 60;
                    return `${minutes}m ${seconds}s`;
                  };
                  
                  return (
                    <TableRow key={sync.id}>
                      <TableCell>
                        {sync.source_instance_name} → {sync.destination_instance_name}
                      </TableCell>
                      <TableCell>
                        <Chip label={sync.sync_type} size="small" />
                      </TableCell>
                      <TableCell>{getStatusChip(sync.sync_status)}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="success.main">
                          {sync.items_synced} synced
                        </Typography>
                        {sync.items_failed > 0 && (
                          <Typography variant="body2" color="error.main">
                            {sync.items_failed} failed
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {formatDuration(sync.duration)}
                      </TableCell>
                      <TableCell>
                        {sync.completed_at
                          ? new Date(sync.completed_at).toLocaleString()
                          : '-'}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Sync Details Dialog */}
      {syncDetails && (
        <Dialog
          open={selectedSync !== null}
          onClose={() => setSelectedSync(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Sync Details</DialogTitle>
          <DialogContent>
            {syncDetails && (
              <List>
                <ListItem>
                  <ListItemText
                    primary="Sync ID"
                    secondary={syncDetails.id}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Source Instance"
                    secondary={syncDetails.source_instance?.name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Destination Instance"
                    secondary={syncDetails.destination_instance?.name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Type"
                    secondary={syncDetails.sync_type}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={syncDetails.sync_status}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Items Synced"
                    secondary={syncDetails.items_synced}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Items Failed"
                    secondary={syncDetails.items_failed}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Started At"
                    secondary={new Date(syncDetails.started_at).toLocaleString()}
                  />
                </ListItem>
                {syncDetails.completed_at && (
                  <ListItem>
                    <ListItemText
                      primary="Completed At"
                      secondary={new Date(syncDetails.completed_at).toLocaleString()}
                    />
                  </ListItem>
                )}
                {syncDetails.error_message && (
                  <ListItem>
                    <ListItemText
                      primary="Error Message"
                      secondary={syncDetails.error_message}
                    />
                  </ListItem>
                )}
              </List>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setSelectedSync(null);
              setSyncDetails(null);
            }}>
              Close
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
}