import React, { useState, useEffect, useRef, ChangeEvent, useCallback } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Divider,
  Input,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  DeleteForever as DeleteIcon,
  CloudUpload as CloudUploadIcon,
  Delete as RemoveIcon,
} from '@mui/icons-material';
import { ApiService, ScrapingStatus } from '../services/api';

interface ScrapingPageProps {
  onDataUpdate: () => void;
}

function ScrapingPage({ onDataUpdate }: ScrapingPageProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<ScrapingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadStatus = useCallback(async () => {
    try {
      const statusData = await ApiService.getScrapingStatus();
      setStatus(prevStatus => {
        // Only update onDataUpdate if status actually changed to completed
        if (prevStatus && prevStatus.status !== statusData.status && 
            statusData.status === 'completed') {
          onDataUpdate();
        }
        return statusData;
      });
      
      // Stop polling if scraping is finished or failed
      if (statusData.status === 'completed' || statusData.status === 'failed' || statusData.status === 'stopped') {
        setIsPolling(false);
      }
      // Start polling if scraping is running or pending
      else if ((statusData.status === 'running' || statusData.status === 'pending') && !isPolling) {
        setIsPolling(true);
      }
    } catch (err) {
      console.error('Error loading status:', err);
    }
  }, [onDataUpdate, isPolling]);

  useEffect(() => {
    // Load status once on mount
    loadStatus();
    return () => {
      // Always clear polling interval on unmount
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };
  }, []);

  useEffect(() => {
    // Start polling when isPolling is true
    if (isPolling) {
      intervalRef.current = setInterval(async () => {
        await loadStatus();
      }, 2000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPolling, loadStatus]);

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newFiles = Array.from(files).filter(file => 
        file.name.toLowerCase().endsWith('.csv')
      );
      
      if (newFiles.length !== files.length) {
        setError('Only CSV files are supported');
      } else {
        setError(null);
      }
      
      setSelectedFiles(newFiles);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const startImport = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one CSV file to import');
      return;
    }

    try {
      setError(null);
      setUploadProgress(0);
      
      // For now, we'll only handle single file upload
      // Multiple files can be added later if needed
      const file = selectedFiles[0];
      
      await ApiService.uploadCSVFile(file, true); // Always incremental
      
      // Start polling
      setIsPolling(true);
      loadStatus();
      
      // Clear selected files after successful upload
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start import');
    }
  };

  const stopScraping = async () => {
    try {
      await ApiService.stopScraping();
      setIsPolling(false);
      loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop scraping');
    }
  };

  const resetData = async () => {
    try {
      await ApiService.resetScrapingData();
      setShowResetDialog(false);
      loadStatus();
      onDataUpdate();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset data');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
      case 'pending':
        return 'primary';
      case 'failed':
      case 'stopped':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'not_started':
        return 'Ready to start';
      case 'pending':
        return 'Starting...';
      case 'running':
        return 'Scraping in progress';
      case 'completed':
        return 'Completed successfully';
      case 'failed':
        return 'Failed';
      case 'stopped':
        return 'Stopped by user';
      default:
        return status;
    }
  };

  const isActive = status?.status === 'running' || status?.status === 'pending';

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Import IMDB Ratings
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload CSV File
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              disabled={isActive}
            />
            <Button
              variant="outlined"
              startIcon={<CloudUploadIcon />}
              onClick={() => fileInputRef.current?.click()}
              disabled={isActive}
              sx={{ mr: 2 }}
            >
              Choose CSV File
            </Button>
            <Typography variant="caption" color="text.secondary">
              Select your IMDb ratings export file (.csv format)
            </Typography>
          </Box>

          {selectedFiles.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Selected Files:
              </Typography>
              <List dense>
                {selectedFiles.map((file, index) => (
                  <ListItem key={index} sx={{ pl: 0 }}>
                    <ListItemText 
                      primary={file.name}
                      secondary={`${(file.size / 1024).toFixed(1)} KB`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => removeFile(index)}
                        disabled={isActive}
                        size="small"
                      >
                        <RemoveIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          
          <Alert severity="info">
            <Typography variant="body2">
              <strong>Incremental Import:</strong> New ratings will be added without removing existing data. 
              Duplicate movies (same IMDb ID) will be skipped to avoid conflicts.
            </Typography>
          </Alert>
        </CardContent>
      </Card>

      {status && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Import Status
              </Typography>
              <Chip 
                label={getStatusText(status.status)}
                color={getStatusColor(status.status) as any}
                variant="outlined"
              />
            </Box>

            {status.total_ratings > 0 && (
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Progress: {status.scraped_ratings} / {status.total_ratings} ratings 
                  ({status.progress_percentage.toFixed(1)}%)
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={status.progress_percentage} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}

            {status.current_movie && (
              <Typography variant="body2" color="text.secondary">
                Currently processing: <strong>{status.current_movie}</strong>
              </Typography>
            )}

            {status.error_message && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {status.error_message}
              </Alert>
            )}

            {status.started_at && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Started: {new Date(status.started_at).toLocaleString()}
              </Typography>
            )}

            {status.completed_at && (
              <Typography variant="caption" display="block">
                Completed: {new Date(status.completed_at).toLocaleString()}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box display="flex" gap={2} flexWrap="wrap">
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={startImport}
          disabled={isActive || selectedFiles.length === 0}
          size="large"
        >
          Import CSV
        </Button>

        <Button
          variant="outlined"
          startIcon={<StopIcon />}
          onClick={stopScraping}
          disabled={!isActive}
          color="error"
        >
          Stop
        </Button>

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadStatus}
          disabled={isActive}
        >
          Refresh Status
        </Button>

        <Button
          variant="outlined"
          startIcon={<DeleteIcon />}
          onClick={() => setShowResetDialog(true)}
          disabled={isActive}
          color="error"
        >
          Reset All Data
        </Button>
      </Box>

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="h6" gutterBottom>
          How to Import Your IMDb Ratings
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          1. <strong>Export from IMDb:</strong> Go to your IMDb ratings page and export your ratings as a CSV file.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          2. <strong>Upload CSV:</strong> Select and upload your downloaded CSV file using the button above.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          3. <strong>Incremental Import:</strong> New movies will be added to your collection without affecting existing data.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          4. <strong>Data Enrichment:</strong> Use the Dashboard to enrich your movies with poster images from TMDb.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> The CSV should contain columns like Const (IMDb ID), Title, Your Rating, Year, Directors, Genres, etc.
        </Typography>
      </Box>

      <Dialog open={showResetDialog} onClose={() => setShowResetDialog(false)}>
        <DialogTitle>Reset All Data</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete all scraped movie data, ratings, and analysis results. 
            Are you sure you want to continue?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResetDialog(false)}>Cancel</Button>
          <Button onClick={resetData} color="error" variant="contained">
            Reset All Data
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ScrapingPage;