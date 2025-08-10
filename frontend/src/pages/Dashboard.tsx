import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Snackbar,
} from '@mui/material';
import {
  Movie as MovieIcon,
  Star as StarIcon,
  DateRange as DateIcon,
  Timer as TimerIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { ApiService, MovieStats } from '../services/api';

interface DashboardProps {
  onDataUpdate: () => void;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
}

function StatCard({ title, value, icon, subtitle }: StatCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h3" component="div" color="primary">
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

function Dashboard({ onDataUpdate }: DashboardProps) {
  const [stats, setStats] = useState<MovieStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [enrichingPosters, setEnrichingPosters] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const statsData = await ApiService.getRatingStats();
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error('Error loading stats:', err);
      setError('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleEnrichPosters = async () => {
    try {
      setEnrichingPosters(true);
      const result = await ApiService.enrichMoviePosters(50);
      setSnackbarMessage(result.message);
      setSnackbarOpen(true);
      
      // Refresh data if movies were updated
      if (result.enriched > 0) {
        onDataUpdate();
      }
    } catch (error: any) {
      console.error('Error enriching posters:', error);
      setSnackbarMessage('Failed to enrich movie posters');
      setSnackbarOpen(true);
    } finally {
      setEnrichingPosters(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!stats || stats.total_ratings === 0) {
    return (
      <Alert severity="info">
        No rating data available. Please import your IMDB ratings first.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Overview
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Ratings"
            value={stats.total_ratings.toLocaleString()}
            icon={<MovieIcon color="primary" />}
            subtitle="Movies you've rated"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Average Rating"
            value={`${stats.average_rating}/10`}
            icon={<StarIcon color="primary" />}
            subtitle="Your overall rating tendency"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Year Range"
            value={`${stats.latest_year - stats.earliest_year + 1} years`}
            icon={<DateIcon color="primary" />}
            subtitle={`${stats.earliest_year} - ${stats.latest_year}`}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Rating Range"
            value={`${stats.min_rating} - ${stats.max_rating}`}
            icon={<TimerIcon color="primary" />}
            subtitle="Your rating scale usage"
          />
        </Grid>
      </Grid>

      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          Quick Insights
        </Typography>
        <Card>
          <CardContent>
            <Typography variant="body1" paragraph>
              You've rated <strong>{stats.total_ratings}</strong> movies with an average rating of{' '}
              <strong>{stats.average_rating}/10</strong>.
            </Typography>
            <Typography variant="body1" paragraph>
              Your ratings span <strong>{stats.unique_years}</strong> different years, from{' '}
              <strong>{stats.earliest_year}</strong> to <strong>{stats.latest_year}</strong>.
            </Typography>
            <Typography variant="body1">
              You use a rating scale from <strong>{stats.min_rating}</strong> to{' '}
              <strong>{stats.max_rating}</strong>, showing{' '}
              {stats.max_rating - stats.min_rating >= 8 ? 'good' : 'limited'} scale utilization.
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Data Management Section */}
      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          Data Management
        </Typography>
        <Card>
          <CardContent>
            <Typography variant="body1" paragraph>
              Enrich your movie collection with high-quality poster images from The Movie Database (TMDb).
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={enrichingPosters ? <CircularProgress size={20} /> : <RefreshIcon />}
              onClick={handleEnrichPosters}
              disabled={enrichingPosters}
            >
              {enrichingPosters ? 'Enriching Posters...' : 'Enrich Movie Posters'}
            </Button>
            <Typography variant="caption" display="block" mt={1} color="text.secondary">
              This will fetch poster images for up to 50 movies without posters.
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
}

export default Dashboard;