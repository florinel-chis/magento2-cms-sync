import React, { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Typography,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  WifiTethering as TestIcon,
  Refresh as RefreshIcon,
  ViewModule as BlocksIcon,
  Article as PagesIcon,
} from '@mui/icons-material';
import useStore from '../store';
import instanceService from '../services/instanceService';
import dataService from '../services/dataService';
import InstanceFormModal from '../components/InstanceFormModal';
import DeleteConfirmDialog from '../components/DeleteConfirmDialog';
import { DataType } from '../types';

interface DataSnapshotInfo {
  [instanceId: number]: {
    blocks?: { count: number; lastUpdated: string };
    pages?: { count: number; lastUpdated: string };
  };
}

export default function Instances() {
  const {
    instances,
    loadingInstances,
    setInstances,
    setLoadingInstances,
    showSnackbar,
  } = useStore();

  const [formModalOpen, setFormModalOpen] = useState(false);
  const [editingInstance, setEditingInstance] = useState<number | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingInstance, setDeletingInstance] = useState<number | null>(null);
  const [testingConnection, setTestingConnection] = useState<number | null>(null);
  const [refreshingData, setRefreshingData] = useState<{ id: number; type: DataType } | null>(null);
  const [dataSnapshots, setDataSnapshots] = useState<DataSnapshotInfo>({});

  const loadInstances = useCallback(async () => {
    try {
      setLoadingInstances(true);
      const data = await instanceService.getAll();
      setInstances(data);
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to load instances', 'error');
    } finally {
      setLoadingInstances(false);
    }
  }, [setLoadingInstances, setInstances, showSnackbar]);

  const loadDataSnapshots = useCallback(async () => {
    try {
      const snapshots = await instanceService.getAllDataSnapshots();
      setDataSnapshots(snapshots);
    } catch (error: any) {
      console.error('Failed to load data snapshots:', error);
    }
  }, []);

  useEffect(() => {
    loadInstances();
  }, [loadInstances]);

  useEffect(() => {
    if (instances.length > 0) {
      loadDataSnapshots();
    }
  }, [instances, loadDataSnapshots]);

  const handleAdd = () => {
    setEditingInstance(null);
    setFormModalOpen(true);
  };

  const handleEdit = (id: number) => {
    setEditingInstance(id);
    setFormModalOpen(true);
  };

  const handleDelete = (id: number) => {
    setDeletingInstance(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = useCallback(async () => {
    if (!deletingInstance) return;

    try {
      await instanceService.delete(deletingInstance);
      showSnackbar('Instance deleted successfully', 'success');
      loadInstances();
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to delete instance', 'error');
    } finally {
      setDeleteDialogOpen(false);
      setDeletingInstance(null);
    }
  }, [deletingInstance, showSnackbar, loadInstances]);

  const handleTestConnection = useCallback(async (id: number) => {
    try {
      setTestingConnection(id);
      const result = await instanceService.testConnection(id);

      if (result.success) {
        showSnackbar('Connection test successful', 'success');
      } else {
        showSnackbar(result.message, 'error');
      }
    } catch (error: any) {
      showSnackbar(error.message || 'Connection test failed', 'error');
    } finally {
      setTestingConnection(null);
    }
  }, [showSnackbar]);

  const handleRefreshData = useCallback(async (id: number, dataType: DataType) => {
    try {
      setRefreshingData({ id, type: dataType });
      const result = await dataService.refreshInstanceData(id, dataType);

      // Update snapshot info
      setDataSnapshots(prev => ({
        ...prev,
        [id]: {
          ...prev[id],
          [dataType]: {
            count: result.item_count,
            lastUpdated: result.created_at,
          }
        }
      }));

      showSnackbar(
        `${dataType === DataType.BLOCKS ? 'Blocks' : 'Pages'} refreshed successfully (${result.item_count} items)`,
        'success'
      );

      // Reload all snapshots to ensure consistency
      loadDataSnapshots();
    } catch (error: any) {
      showSnackbar(error.message || `Failed to refresh ${dataType}`, 'error');
    } finally {
      setRefreshingData(null);
    }
  }, [showSnackbar, loadDataSnapshots]);

  if (loadingInstances) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Magento Instances</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAdd}
        >
          Add Instance
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Data</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {instances.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No instances configured. Click "Add Instance" to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              instances.map((instance) => (
                <TableRow key={instance.id}>
                  <TableCell>{instance.name}</TableCell>
                  <TableCell>{instance.url}</TableCell>
                  <TableCell>
                    <Chip
                      icon={instance.is_active ? <CheckIcon /> : <CloseIcon />}
                      label={instance.is_active ? 'Active' : 'Inactive'}
                      color={instance.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(instance.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" gap={1} justifyContent="center">
                      <Tooltip title={
                        dataSnapshots[instance.id]?.blocks 
                          ? `Blocks: ${dataSnapshots[instance.id].blocks!.count} items (Last updated: ${new Date(dataSnapshots[instance.id].blocks!.lastUpdated).toLocaleString()})`
                          : "Refresh CMS Blocks"
                      }>
                        <Box position="relative" display="inline-flex">
                          <IconButton
                            size="small"
                            onClick={() => handleRefreshData(instance.id, DataType.BLOCKS)}
                            disabled={refreshingData?.id === instance.id && refreshingData?.type === DataType.BLOCKS}
                          >
                            {refreshingData?.id === instance.id && refreshingData?.type === DataType.BLOCKS ? (
                              <CircularProgress size={20} />
                            ) : (
                              <BlocksIcon />
                            )}
                          </IconButton>
                          {dataSnapshots[instance.id]?.blocks && (
                            <Box
                              position="absolute"
                              top={-4}
                              right={-4}
                              bgcolor="primary.main"
                              color="white"
                              borderRadius="10px"
                              px={0.5}
                              fontSize="0.7rem"
                              minWidth="18px"
                              textAlign="center"
                            >
                              {dataSnapshots[instance.id].blocks!.count}
                            </Box>
                          )}
                        </Box>
                      </Tooltip>
                      <Tooltip title={
                        dataSnapshots[instance.id]?.pages 
                          ? `Pages: ${dataSnapshots[instance.id].pages!.count} items (Last updated: ${new Date(dataSnapshots[instance.id].pages!.lastUpdated).toLocaleString()})`
                          : "Refresh CMS Pages"
                      }>
                        <Box position="relative" display="inline-flex">
                          <IconButton
                            size="small"
                            onClick={() => handleRefreshData(instance.id, DataType.PAGES)}
                            disabled={refreshingData?.id === instance.id && refreshingData?.type === DataType.PAGES}
                          >
                            {refreshingData?.id === instance.id && refreshingData?.type === DataType.PAGES ? (
                              <CircularProgress size={20} />
                            ) : (
                              <PagesIcon />
                            )}
                          </IconButton>
                          {dataSnapshots[instance.id]?.pages && (
                            <Box
                              position="absolute"
                              top={-4}
                              right={-4}
                              bgcolor="primary.main"
                              color="white"
                              borderRadius="10px"
                              px={0.5}
                              fontSize="0.7rem"
                              minWidth="18px"
                              textAlign="center"
                            >
                              {dataSnapshots[instance.id].pages!.count}
                            </Box>
                          )}
                        </Box>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Test Connection">
                      <IconButton
                        size="small"
                        onClick={() => handleTestConnection(instance.id)}
                        disabled={testingConnection === instance.id}
                      >
                        {testingConnection === instance.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <TestIcon />
                        )}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(instance.id)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(instance.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <InstanceFormModal
        open={formModalOpen}
        onClose={() => setFormModalOpen(false)}
        instanceId={editingInstance}
        onSuccess={loadInstances}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Instance"
        message="Are you sure you want to delete this instance? This action cannot be undone."
      />
    </Box>
  );
}