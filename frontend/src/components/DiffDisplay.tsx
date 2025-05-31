import React from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import * as Diff from 'diff';

interface DiffDisplayProps {
  oldValue: string;
  newValue: string;
  title?: string;
  splitView?: boolean;
}

export default function DiffDisplay({ oldValue, newValue, title, splitView = false }: DiffDisplayProps) {
  const theme = useTheme();
  
  if (splitView) {
    // Split view - side by side
    const lines = Diff.diffLines(oldValue, newValue);
    const oldLines: Array<{ content: string; type: 'removed' | 'normal' }> = [];
    const newLines: Array<{ content: string; type: 'added' | 'normal' }> = [];
    
    lines.forEach(part => {
      const lines = part.value.split('\n').filter(line => line !== '');
      if (part.added) {
        lines.forEach(line => {
          newLines.push({ content: line, type: 'added' });
          oldLines.push({ content: '', type: 'normal' });
        });
      } else if (part.removed) {
        lines.forEach(line => {
          oldLines.push({ content: line, type: 'removed' });
          newLines.push({ content: '', type: 'normal' });
        });
      } else {
        lines.forEach(line => {
          oldLines.push({ content: line, type: 'normal' });
          newLines.push({ content: line, type: 'normal' });
        });
      }
    });
    
    return (
      <Box>
        {title && (
          <Typography variant="subtitle2" gutterBottom>
            {title}
          </Typography>
        )}
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1}>
          <Box>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block',
                bgcolor: theme.palette.error.light,
                color: theme.palette.error.contrastText,
                px: 2,
                py: 0.5,
                fontWeight: 'bold'
              }}
            >
              Source
            </Typography>
            <Box
              sx={{
                bgcolor: theme.palette.grey[50],
                border: `1px solid ${theme.palette.divider}`,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                maxHeight: 400,
                overflow: 'auto',
              }}
            >
              {oldLines.map((line, index) => (
                <Box
                  key={index}
                  sx={{
                    minHeight: '1.5em',
                    px: 2,
                    py: 0.25,
                    bgcolor: line.type === 'removed' 
                      ? theme.palette.error.light + '40'
                      : 'transparent',
                    borderLeft: line.type === 'removed'
                      ? `3px solid ${theme.palette.error.main}`
                      : '3px solid transparent',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {line.content || '\u00A0'}
                </Box>
              ))}
            </Box>
          </Box>
          
          <Box>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block',
                bgcolor: theme.palette.success.light,
                color: theme.palette.success.contrastText,
                px: 2,
                py: 0.5,
                fontWeight: 'bold'
              }}
            >
              Destination
            </Typography>
            <Box
              sx={{
                bgcolor: theme.palette.grey[50],
                border: `1px solid ${theme.palette.divider}`,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                maxHeight: 400,
                overflow: 'auto',
              }}
            >
              {newLines.map((line, index) => (
                <Box
                  key={index}
                  sx={{
                    minHeight: '1.5em',
                    px: 2,
                    py: 0.25,
                    bgcolor: line.type === 'added' 
                      ? theme.palette.success.light + '40'
                      : 'transparent',
                    borderLeft: line.type === 'added'
                      ? `3px solid ${theme.palette.success.main}`
                      : '3px solid transparent',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {line.content || '\u00A0'}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>
    );
  }
  
  // Unified view
  const diff = Diff.diffWords(oldValue, newValue);
  
  return (
    <Box>
      {title && (
        <Typography variant="subtitle2" gutterBottom>
          {title}
        </Typography>
      )}
      <Box
        sx={{
          bgcolor: theme.palette.grey[50],
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 1,
          p: 2,
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          maxHeight: 400,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {diff.map((part, index) => (
          <Box
            key={index}
            component="span"
            sx={{
              backgroundColor: part.added
                ? theme.palette.success.light + '60'
                : part.removed
                ? theme.palette.error.light + '60'
                : 'transparent',
              textDecoration: part.removed ? 'line-through' : 'none',
              color: part.removed ? theme.palette.error.dark : 'inherit',
            }}
          >
            {part.value}
          </Box>
        ))}
      </Box>
    </Box>
  );
}