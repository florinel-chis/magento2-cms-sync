import React from 'react';
import { Snackbar, Alert } from '@mui/material';
import useStore from '../store';

export default function NotificationSnackbar() {
  const { snackbar, hideSnackbar } = useStore();

  return (
    <Snackbar
      open={snackbar.open}
      autoHideDuration={6000}
      onClose={hideSnackbar}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        onClose={hideSnackbar}
        severity={snackbar.severity}
        sx={{ width: '100%' }}
        variant="filled"
      >
        {snackbar.message}
      </Alert>
    </Snackbar>
  );
}