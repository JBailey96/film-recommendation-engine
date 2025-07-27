import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  Rating,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Star as StarIcon } from '@mui/icons-material';
import { useDebounce } from 'use-debounce';
import { ApiService, Rating as RatingType, RatingsSearchParams, MovieStats } from '../services/api';
import SearchAndFilters, { FilterState } from '../components/SearchAndFilters';
import ViewToggle, { ViewMode } from '../components/ViewToggle';
import MovieGrid from '../components/MovieGrid';
import MovieDetailModal from '../components/MovieDetailModal';

function RatingsPage() {
  // Data state
  const [ratings, setRatings] = useState<RatingType[]>([]);
  const [totalRatings, setTotalRatings] = useState(0);
  const [availableGenres, setAvailableGenres] = useState<string[]>([]);
  const [stats, setStats] = useState<MovieStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(24);
  const [selectedMovie, setSelectedMovie] = useState<RatingType | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    genres: [],
    yearRange: [1900, 2024],
    userRatingRange: [1, 10],
    imdbRatingRange: [0, 10],
    runtimeRange: [0, 300],
    sortBy: 'rated_at',
    order: 'desc',
  });

  // Debounced search to avoid too many API calls
  const [debouncedSearch] = useDebounce(filters.search, 500);

  // Initialize data
  useEffect(() => {
    initializeData();
  }, []);

  // Load ratings when filters or pagination change
  useEffect(() => {
    loadRatings();
  }, [
    debouncedSearch,
    filters.genres,
    filters.yearRange,
    filters.userRatingRange,
    filters.imdbRatingRange,
    filters.runtimeRange,
    filters.sortBy,
    filters.order,
    currentPage,
    itemsPerPage,
  ]);

  const initializeData = async () => {
    try {
      setLoading(true);
      const [genresData, statsData] = await Promise.all([
        ApiService.getAvailableGenres(),
        ApiService.getRatingStats(),
      ]);
      
      setAvailableGenres(genresData);
      setStats(statsData);
      
      // Update year range based on actual data
      if (statsData.earliest_year && statsData.latest_year) {
        setFilters(prev => ({
          ...prev,
          yearRange: [statsData.earliest_year, statsData.latest_year],
        }));
      }
    } catch (err) {
      console.error('Failed to initialize data:', err);
      setError('Failed to load initial data');
    } finally {
      setLoading(false);
    }
  };

  const loadRatings = async () => {
    if (!stats) return; // Wait for stats to be loaded first
    
    try {
      setLoading(true);
      
      const params: RatingsSearchParams = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        sort_by: filters.sortBy,
        order: filters.order,
      };

      // Add search parameter
      if (debouncedSearch.trim()) {
        params.search = debouncedSearch.trim();
      }

      // Add genre filters
      if (filters.genres.length > 0) {
        params.genres = filters.genres;
      }

      // Add range filters (only if different from defaults)
      if (filters.yearRange[0] !== stats.earliest_year || filters.yearRange[1] !== stats.latest_year) {
        params.year_min = filters.yearRange[0];
        params.year_max = filters.yearRange[1];
      }

      if (filters.userRatingRange[0] !== 1 || filters.userRatingRange[1] !== 10) {
        params.rating_min = filters.userRatingRange[0];
        params.rating_max = filters.userRatingRange[1];
      }

      if (filters.imdbRatingRange[0] !== 0 || filters.imdbRatingRange[1] !== 10) {
        params.imdb_rating_min = filters.imdbRatingRange[0];
        params.imdb_rating_max = filters.imdbRatingRange[1];
      }

      if (filters.runtimeRange[0] !== 0 || filters.runtimeRange[1] !== 300) {
        params.runtime_min = filters.runtimeRange[0];
        params.runtime_max = filters.runtimeRange[1];
      }

      const data = await ApiService.getAllRatings(params);
      setRatings(data.ratings);
      setTotalRatings(data.total);
      setError(null);
    } catch (err: any) {
      setError('Failed to load ratings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Event handlers
  const handleFiltersChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  const handleClearFilters = useCallback(() => {
    if (!stats) return;
    
    setFilters({
      search: '',
      genres: [],
      yearRange: [stats.earliest_year, stats.latest_year],
      userRatingRange: [1, 10],
      imdbRatingRange: [0, 10],
      runtimeRange: [0, 300],
      sortBy: 'rated_at',
      order: 'desc',
    });
    setCurrentPage(1);
  }, [stats]);

  const handleMovieClick = useCallback((rating: RatingType) => {
    setSelectedMovie(rating);
    setModalOpen(true);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleItemsPerPageChange = useCallback((itemsPerPage: number) => {
    setItemsPerPage(itemsPerPage);
    setCurrentPage(1);
  }, []);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'success';
    if (rating >= 6) return 'warning';
    return 'error';
  };

  // Render list view table
  const renderListView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Poster</TableCell>
            <TableCell>Movie</TableCell>
            <TableCell>Year</TableCell>
            <TableCell>Genres</TableCell>
            <TableCell>Director</TableCell>
            <TableCell>My Rating</TableCell>
            <TableCell>IMDB Rating</TableCell>
            <TableCell>Date Rated</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {ratings.map((rating) => (
            <TableRow 
              key={rating.movie.id} 
              hover 
              sx={{ cursor: 'pointer' }}
              onClick={() => handleMovieClick(rating)}
            >
              <TableCell>
                {rating.movie.poster_url ? (
                  <Avatar
                    src={rating.movie.poster_url}
                    variant="rounded"
                    sx={{ width: 40, height: 60 }}
                  />
                ) : (
                  <Avatar variant="rounded" sx={{ width: 40, height: 60 }}>
                    ?
                  </Avatar>
                )}
              </TableCell>
              <TableCell>
                <Typography variant="subtitle2">
                  {rating.movie.title}
                </Typography>
                {rating.movie.runtime_minutes && (
                  <Typography variant="caption" color="text.secondary">
                    {rating.movie.runtime_minutes} min
                  </Typography>
                )}
              </TableCell>
              <TableCell>{rating.movie.year || 'N/A'}</TableCell>
              <TableCell>
                <Box display="flex" gap={0.5} flexWrap="wrap">
                  {rating.movie.genres?.slice(0, 3).map((genre) => (
                    <Chip 
                      key={genre} 
                      label={genre} 
                      size="small" 
                      variant="outlined"
                    />
                  ))}
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {rating.movie.director || 'N/A'}
                </Typography>
              </TableCell>
              <TableCell>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={rating.rating}
                    color={getRatingColor(rating.rating) as any}
                    size="small"
                  />
                  <Rating
                    value={rating.rating / 2}
                    readOnly
                    size="small"
                    max={5}
                  />
                </Box>
              </TableCell>
              <TableCell>
                {rating.movie.imdb_rating ? (
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <StarIcon fontSize="small" color="warning" />
                    <Typography variant="body2">
                      {rating.movie.imdb_rating}
                    </Typography>
                  </Box>
                ) : (
                  'N/A'
                )}
              </TableCell>
              <TableCell>
                {formatDate(rating.rated_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (loading && !stats) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Movie Collection Browser
      </Typography>
      
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Browse and search through your {stats?.total_ratings || 0} rated movies
      </Typography>

      {/* Search and Filters */}
      {stats && (
        <SearchAndFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          availableGenres={availableGenres}
          yearRange={[stats.earliest_year, stats.latest_year]}
          onClearFilters={handleClearFilters}
        />
      )}

      {/* View Controls */}
      <ViewToggle
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        totalItems={totalRatings}
        currentPage={currentPage}
        itemsPerPage={itemsPerPage}
        onPageChange={handlePageChange}
        onItemsPerPageChange={handleItemsPerPageChange}
        loading={loading}
      />

      {/* Results */}
      {loading ? (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      ) : ratings.length === 0 ? (
        <Box textAlign="center" mt={4}>
          <Typography variant="h6" color="text.secondary">
            No movies found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search criteria or filters
          </Typography>
        </Box>
      ) : (
        <Box sx={{ mb: 4 }}>
          {viewMode === 'grid' ? (
            <MovieGrid
              ratings={ratings}
              onMovieClick={handleMovieClick}
              loading={loading}
            />
          ) : (
            renderListView()
          )}
        </Box>
      )}

      {/* Movie Detail Modal */}
      <MovieDetailModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        rating={selectedMovie}
      />
    </Box>
  );
}

export default RatingsPage;