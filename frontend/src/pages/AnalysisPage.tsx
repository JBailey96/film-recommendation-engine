import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemText,
  Button,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

import { ApiService } from '../services/api';
import type {
  GenreAnalysis,
  YearAnalysis,
  RuntimeAnalysis,
  CastAnalysis,
  PosterStyleAnalysis,
  OverallInsights,
} from '../services/api';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0'];

interface AnalysisCardProps {
  title: string;
  children: React.ReactNode;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
}

function AnalysisCard({ title, children, loading, error, onRefresh }: AnalysisCardProps) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{title}</Typography>
          {onRefresh && (
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={onRefresh}
              disabled={loading}
            >
              Refresh
            </Button>
          )}
        </Box>
        
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}

function AnalysisPage() {
  const [genreAnalysis, setGenreAnalysis] = useState<GenreAnalysis | null>(null);
  const [yearAnalysis, setYearAnalysis] = useState<YearAnalysis | null>(null);
  const [runtimeAnalysis, setRuntimeAnalysis] = useState<RuntimeAnalysis | null>(null);
  const [castAnalysis, setCastAnalysis] = useState<CastAnalysis | null>(null);
  const [posterAnalysis, setPosterAnalysis] = useState<PosterStyleAnalysis | null>(null);
  const [overallInsights, setOverallInsights] = useState<OverallInsights | null>(null);
  
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadAllAnalysis();
  }, []);

  const loadAllAnalysis = () => {
    loadGenreAnalysis();
    loadYearAnalysis();
    loadRuntimeAnalysis();
    loadCastAnalysis();
    loadPosterAnalysis();
    loadOverallInsights();
  };

  const setLoadingState = (key: string, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  };

  const setError = (key: string, error: string) => {
    setErrors(prev => ({ ...prev, [key]: error }));
  };

  const loadGenreAnalysis = async () => {
    try {
      setLoadingState('genres', true);
      const data = await ApiService.getGenreAnalysis();
      setGenreAnalysis(data);
      setError('genres', '');
    } catch (err: any) {
      setError('genres', 'Failed to load genre analysis');
    } finally {
      setLoadingState('genres', false);
    }
  };

  const loadYearAnalysis = async () => {
    try {
      setLoadingState('years', true);
      const data = await ApiService.getYearAnalysis();
      setYearAnalysis(data);
      setError('years', '');
    } catch (err: any) {
      setError('years', 'Failed to load year analysis');
    } finally {
      setLoadingState('years', false);
    }
  };

  const loadRuntimeAnalysis = async () => {
    try {
      setLoadingState('runtime', true);
      const data = await ApiService.getRuntimeAnalysis();
      setRuntimeAnalysis(data);
      setError('runtime', '');
    } catch (err: any) {
      setError('runtime', 'Failed to load runtime analysis');
    } finally {
      setLoadingState('runtime', false);
    }
  };

  const loadCastAnalysis = async () => {
    try {
      setLoadingState('cast', true);
      const data = await ApiService.getCastAnalysis();
      setCastAnalysis(data);
      setError('cast', '');
    } catch (err: any) {
      setError('cast', 'Failed to load cast analysis');
    } finally {
      setLoadingState('cast', false);
    }
  };

  const loadPosterAnalysis = async () => {
    try {
      setLoadingState('poster', true);
      const data = await ApiService.getPosterAnalysis();
      setPosterAnalysis(data);
      setError('poster', '');
    } catch (err: any) {
      setError('poster', 'Failed to load poster analysis');
    } finally {
      setLoadingState('poster', false);
    }
  };

  const loadOverallInsights = async () => {
    try {
      setLoadingState('insights', true);
      const data = await ApiService.getOverallInsights();
      setOverallInsights(data);
      setError('insights', '');
    } catch (err: any) {
      setError('insights', 'Failed to load overall insights');
    } finally {
      setLoadingState('insights', false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Your Movie Preferences Analysis
      </Typography>

      {/* Overall Insights */}
      <AnalysisCard
        title="Overall Insights"
        loading={loading.insights}
        error={errors.insights}
        onRefresh={loadOverallInsights}
      >
        {overallInsights && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Personality Profile</Typography>
              <Typography variant="body1" paragraph>
                {overallInsights.personality_profile}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Viewing Patterns</Typography>
              <Typography variant="body1" paragraph>
                {overallInsights.viewing_patterns}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Recommendations</Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                {overallInsights.recommendations.map((rec, index) => (
                  <Chip key={index} label={rec} color="primary" variant="outlined" />
                ))}
              </Box>
            </Grid>
            {overallInsights.claude_analysis && (
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">AI Deep Analysis</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body1" style={{ whiteSpace: 'pre-line' }}>
                      {overallInsights.claude_analysis}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              </Grid>
            )}
          </Grid>
        )}
      </AnalysisCard>

      {/* Genre Analysis */}
      <AnalysisCard
        title="Genre Preferences"
        loading={loading.genres}
        error={errors.genres}
        onRefresh={loadGenreAnalysis}
      >
        {genreAnalysis && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="subtitle1" gutterBottom>Favorite Genres</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={genreAnalysis.favorite_genres.slice(0, 8)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="genre" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="average_rating" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom>Genre Distribution</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(genreAnalysis.genre_distribution)
                      .map(([genre, count]) => ({ genre, count }))
                      .slice(0, 6)
                    }
                    dataKey="count"
                    nameKey="genre"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                  >
                    {Object.entries(genreAnalysis.genre_distribution).slice(0, 6).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body1" className="insights-text">
                {genreAnalysis.insights}
              </Typography>
            </Grid>
          </Grid>
        )}
      </AnalysisCard>

      {/* Year/Decade Analysis */}
      <AnalysisCard
        title="Year & Decade Preferences"
        loading={loading.years}
        error={errors.years}
        onRefresh={loadYearAnalysis}
      >
        {yearAnalysis && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="subtitle1" gutterBottom>Decade Preferences</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={yearAnalysis.decade_preferences}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="decade" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="average_rating" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom>Favorite Decades</Typography>
              <List>
                {yearAnalysis.favorite_decades.map((decade, index) => (
                  <ListItem key={decade}>
                    <ListItemText 
                      primary={decade} 
                      secondary={`#${index + 1} preference`}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body1" className="insights-text">
                {yearAnalysis.insights}
              </Typography>
            </Grid>
          </Grid>
        )}
      </AnalysisCard>

      {/* Runtime Analysis */}
      <AnalysisCard
        title="Runtime Preferences"
        loading={loading.runtime}
        error={errors.runtime}
        onRefresh={loadRuntimeAnalysis}
      >
        {runtimeAnalysis && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="subtitle1" gutterBottom>Runtime Distribution</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={runtimeAnalysis.runtime_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="runtime_range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="average_rating" fill="#ffc658" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom>Quick Stats</Typography>
              <List>
                <ListItem>
                  <ListItemText 
                    primary="Preferred Length" 
                    secondary={runtimeAnalysis.preferred_length}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Average Runtime" 
                    secondary={`${runtimeAnalysis.average_runtime} minutes`}
                  />
                </ListItem>
              </List>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body1" className="insights-text">
                {runtimeAnalysis.insights}
              </Typography>
            </Grid>
          </Grid>
        )}
      </AnalysisCard>

      {/* Cast Analysis */}
      <AnalysisCard
        title="Favorite Cast & Crew"
        loading={loading.cast}
        error={errors.cast}
        onRefresh={loadCastAnalysis}
      >
        {castAnalysis && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Favorite Actors</Typography>
              <List>
                {castAnalysis.favorite_actors.slice(0, 5).map((actor, index) => (
                  <ListItem key={actor.name}>
                    <ListItemText 
                      primary={actor.name}
                      secondary={`${actor.count} movies, avg rating: ${actor.average_rating}/10`}
                    />
                  </ListItem>
                ))}
              </List>
              <Typography variant="body2" color="text.secondary">
                {castAnalysis.actor_insights}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Favorite Directors</Typography>
              <List>
                {castAnalysis.favorite_directors.slice(0, 5).map((director, index) => (
                  <ListItem key={director.name}>
                    <ListItemText 
                      primary={director.name}
                      secondary={`${director.count} movies, avg rating: ${director.average_rating}/10`}
                    />
                  </ListItem>
                ))}
              </List>
              <Typography variant="body2" color="text.secondary">
                {castAnalysis.director_insights}
              </Typography>
            </Grid>
          </Grid>
        )}
      </AnalysisCard>

      {/* Poster Style Analysis */}
      <AnalysisCard
        title="Visual Style Preferences"
        loading={loading.poster}
        error={errors.poster}
        onRefresh={loadPosterAnalysis}
      >
        {posterAnalysis && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Color Preferences</Typography>
              <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                {posterAnalysis.dominant_colors.slice(0, 6).map((color, index) => (
                  <Chip 
                    key={color.color_name}
                    label={`${color.color_name} (${color.average_rating}/10)`}
                    style={{ 
                      backgroundColor: `rgb(${color.rgb_values.join(',')})`,
                      color: color.rgb_values.reduce((a, b) => a + b, 0) / 3 > 128 ? 'black' : 'white'
                    }}
                  />
                ))}
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Style Preferences</Typography>
              <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                {posterAnalysis.style_preferences.slice(0, 6).map((style) => (
                  <Chip 
                    key={style.style}
                    label={`${style.style} (${style.average_rating}/10)`}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body1" className="insights-text">
                {posterAnalysis.insights}
              </Typography>
              {posterAnalysis.claude_analysis && (
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">AI Visual Analysis</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body1" style={{ whiteSpace: 'pre-line' }}>
                      {posterAnalysis.claude_analysis}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              )}
            </Grid>
          </Grid>
        )}
      </AnalysisCard>
    </Box>
  );
}

export default AnalysisPage;