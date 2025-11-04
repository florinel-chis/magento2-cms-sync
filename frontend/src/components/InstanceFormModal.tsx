import React, { useEffect, useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControlLabel,
  Switch,
  CircularProgress,
} from '@mui/material';
import { Instance, InstanceCreate, InstanceUpdate } from '../types';
import instanceService from '../services/instanceService';
import useStore from '../store';

interface InstanceFormModalProps {
  open: boolean;
  onClose: () => void;
  instanceId: number | null;
  onSuccess: () => void;
}

export default function InstanceFormModal({
  open,
  onClose,
  instanceId,
  onSuccess,
}: InstanceFormModalProps) {
  const { showSnackbar } = useStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    api_token: '',
    is_active: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const loadInstance = useCallback(async () => {
    if (!instanceId) return;

    try {
      setLoading(true);
      const instance = await instanceService.getById(instanceId);
      setFormData({
        name: instance.name,
        url: instance.url,
        api_token: instance.api_token,
        is_active: instance.is_active,
      });
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to load instance', 'error');
      onClose();
    } finally {
      setLoading(false);
    }
  }, [instanceId, showSnackbar, onClose]);

  useEffect(() => {
    if (open && instanceId) {
      loadInstance();
    } else if (open) {
      // Reset form for new instance
      setFormData({
        name: '',
        url: '',
        api_token: '',
        is_active: true,
      });
      setErrors({});
    }
  }, [open, instanceId, loadInstance]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.url.trim()) {
      newErrors.url = 'URL is required';
    } else {
      try {
        new URL(formData.url);
      } catch {
        newErrors.url = 'Invalid URL format';
      }
    }

    if (!formData.api_token.trim()) {
      newErrors.api_token = 'API token is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      setLoading(true);
      
      if (instanceId) {
        // Update existing instance
        const updateData: InstanceUpdate = {
          name: formData.name,
          url: formData.url,
          api_token: formData.api_token,
          is_active: formData.is_active,
        };
        await instanceService.update(instanceId, updateData);
        showSnackbar('Instance updated successfully', 'success');
      } else {
        // Create new instance
        const createData: InstanceCreate = {
          name: formData.name,
          url: formData.url,
          api_token: formData.api_token,
          is_active: formData.is_active,
        };
        await instanceService.create(createData);
        showSnackbar('Instance created successfully', 'success');
      }

      onSuccess();
      onClose();
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to save instance', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {instanceId ? 'Edit Instance' : 'Add New Instance'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Instance Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              error={!!errors.name}
              helperText={errors.name}
              fullWidth
              required
              disabled={loading}
            />
            <TextField
              label="Magento URL"
              value={formData.url}
              onChange={(e) => handleChange('url', e.target.value)}
              error={!!errors.url}
              helperText={errors.url || 'e.g., https://magento.example.com'}
              fullWidth
              required
              disabled={loading}
            />
            <TextField
              label="API Token"
              value={formData.api_token}
              onChange={(e) => handleChange('api_token', e.target.value)}
              error={!!errors.api_token}
              helperText={errors.api_token}
              fullWidth
              required
              disabled={loading}
              type="password"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => handleChange('is_active', e.target.checked)}
                  disabled={loading}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : instanceId ? (
              'Update'
            ) : (
              'Create'
            )}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}