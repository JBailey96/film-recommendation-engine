import React, { useState, useEffect, useRef } from 'react';
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
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  DeleteForever as DeleteIcon,
} from '@mui/icons-material';
import { ApiService, ScrapingStatus } from '../services/api';

interface ScrapingPageProps {
  onDataUpdate: () => void;
}

function ScrapingPage({ onDataUpdate }: ScrapingPageProps) {
  const [imdbUrl, setImdbUrl] = useState('https://www.imdb.com/user/ur34563842/ratings/?ref_=hm_nv_rat');
  const [claudeApiKey, setClaudeApiKey] = useState('');
  const [status, setStatus] = useState<ScrapingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadStatus();
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (status?.status === 'running' || status?.status === 'pending') {
      // Poll every 2 seconds while scraping
      intervalRef.current = setInterval(loadStatus, 2000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [status?.status]);

  const loadStatus = async () => {
    try {
      const statusData = await ApiService.getScrapingStatus();
      setStatus(statusData);
      
      if (statusData.status === 'completed') {
        onDataUpdate();
      }
    } catch (err) {
      console.error('Error loading status:', err);
    }
  };

  const startScraping = async () => {
    try {
      setError(null);
      await ApiService.startScraping({
        imdb_profile_url: imdbUrl,
        claude_api_key: claudeApiKey || undefined,
      });
      
      // Start polling immediately
      loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scraping');
    }
  };

  const stopScraping = async () => {
    try {
      await ApiService.stopScraping();
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
            Configuration
          </Typography>
          
          <TextField
            fullWidth
            label="IMDB Profile URL"
            value={imdbUrl}
            onChange={(e) => setImdbUrl(e.target.value)}
            placeholder="https://www.imdb.com/user/ur12345678/ratings/"
            disabled={isActive}
            sx={{ mb: 2 }}
            helperText="Your public IMDB ratings page URL"
          />
          
          <TextField
            fullWidth
            label="Claude API Key (Optional)"
            type="password"
            value={claudeApiKey}
            onChange={(e) => setClaudeApiKey(e.target.value)}
            disabled={isActive}
            helperText="For advanced poster and preference analysis"
          />
        </CardContent>
      </Card>

      {status && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Scraping Status
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
          startIcon={<PlayIcon />}
          onClick={startScraping}
          disabled={isActive || !imdbUrl.trim()}
          size="large"
        >
          Start Scraping
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
          How it works
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          1. <strong>Data Collection:</strong> We'll scrape your public IMDB ratings page to collect your movie ratings and basic movie information.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          2. <strong>Movie Details:</strong> For each rated movie, we'll fetch detailed information including cast, crew, genres, runtime, and poster images.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          3. <strong>Analysis:</strong> We'll analyze your preferences across genres, years, runtime, cast members, and visual styles.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          4. <strong>AI Insights:</strong> If you provide a Claude API key, we'll generate deep insights about your movie preferences and personality.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> This process respects IMDB's rate limits and may take several minutes depending on your number of ratings.
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