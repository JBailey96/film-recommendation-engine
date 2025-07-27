import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Slider,
  Typography,
  Grid,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Clear as ClearIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { SelectChangeEvent } from '@mui/material/Select';

export interface FilterState {
  search: string;
  genres: string[];
  yearRange: [number, number];
  userRatingRange: [number, number];
  imdbRatingRange: [number, number];
  runtimeRange: [number, number];
  sortBy: string;
  order: string;
}

interface SearchAndFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  availableGenres: string[];
  yearRange: [number, number];
  onClearFilters: () => void;
}

const SORT_OPTIONS = [
  { value: 'rated_at', label: 'Date Rated' },
  { value: 'rating', label: 'My Rating' },
  { value: 'title', label: 'Title' },
  { value: 'year', label: 'Year' },
  { value: 'imdb_rating', label: 'IMDB Rating' },
  { value: 'runtime_minutes', label: 'Runtime' },
];

const SearchAndFilters: React.FC<SearchAndFiltersProps> = ({
  filters,
  onFiltersChange,
  availableGenres,
  yearRange,
  onClearFilters,
}) => {
  const [expanded, setExpanded] = useState<string | false>('search');

  const handleChange = (field: keyof FilterState, value: any) => {
    onFiltersChange({
      ...filters,
      [field]: value,
    });
  };

  const handleGenreChange = (event: SelectChangeEvent<typeof filters.genres>) => {
    const value = event.target.value;
    handleChange('genres', typeof value === 'string' ? value.split(',') : value);
  };

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpanded(isExpanded ? panel : false);
  };

  const hasActiveFilters = () => {
    return (
      filters.search !== '' ||
      filters.genres.length > 0 ||
      filters.yearRange[0] !== yearRange[0] ||
      filters.yearRange[1] !== yearRange[1] ||
      filters.userRatingRange[0] !== 1 ||
      filters.userRatingRange[1] !== 10 ||
      filters.imdbRatingRange[0] !== 0 ||
      filters.imdbRatingRange[1] !== 10 ||
      filters.runtimeRange[0] !== 0 ||
      filters.runtimeRange[1] !== 300
    );
  };

  return (
    <Paper sx={{ mb: 3 }}>
      {/* Search Bar - Always Visible */}
      <Box sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search movies"
              value={filters.search}
              onChange={(e) => handleChange('search', e.target.value)}
              placeholder="Title, director, cast member..."
              InputProps={{
                startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                endAdornment: filters.search && (
                  <IconButton
                    size="small"
                    onClick={() => handleChange('search', '')}
                  >
                    <ClearIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid item xs={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Sort by</InputLabel>
              <Select
                value={filters.sortBy}
                onChange={(e) => handleChange('sortBy', e.target.value)}
                label="Sort by"
              >
                {SORT_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Order</InputLabel>
              <Select
                value={filters.order}
                onChange={(e) => handleChange('order', e.target.value)}
                label="Order"
              >
                <MenuItem value="desc">Descending</MenuItem>
                <MenuItem value="asc">Ascending</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              {hasActiveFilters() && (
                <Tooltip title="Clear all filters">
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={onClearFilters}
                    startIcon={<ClearIcon />}
                  >
                    Clear
                  </Button>
                </Tooltip>
              )}
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Advanced Filters - Expandable */}
      <Accordion expanded={expanded === 'filters'} onChange={handleAccordionChange('filters')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">
            Advanced Filters
            {hasActiveFilters() && (
              <Chip
                label={`${filters.genres.length > 0 ? filters.genres.length + ' genre(s)' : ''} filters active`}
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {/* Genres */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Genres</InputLabel>
                <Select
                  multiple
                  value={filters.genres}
                  onChange={handleGenreChange}
                  input={<OutlinedInput label="Genres" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                  MenuProps={{
                    PaperProps: {
                      style: {
                        maxHeight: 224,
                        width: 250,
                      },
                    },
                  }}
                >
                  {availableGenres.map((genre) => (
                    <MenuItem key={genre} value={genre}>
                      {genre}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Year Range */}
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                Release Year: {filters.yearRange[0]} - {filters.yearRange[1]}
              </Typography>
              <Slider
                value={filters.yearRange}
                onChange={(_, newValue) => handleChange('yearRange', newValue as [number, number])}
                valueLabelDisplay="auto"
                min={yearRange[0]}
                max={yearRange[1]}
                marks={[
                  { value: yearRange[0], label: yearRange[0].toString() },
                  { value: yearRange[1], label: yearRange[1].toString() },
                ]}
              />
            </Grid>

            {/* User Rating Range */}
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                My Rating: {filters.userRatingRange[0]} - {filters.userRatingRange[1]}
              </Typography>
              <Slider
                value={filters.userRatingRange}
                onChange={(_, newValue) => handleChange('userRatingRange', newValue as [number, number])}
                valueLabelDisplay="auto"
                min={1}
                max={10}
                marks={[
                  { value: 1, label: '1' },
                  { value: 5, label: '5' },
                  { value: 10, label: '10' },
                ]}
              />
            </Grid>

            {/* IMDB Rating Range */}
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                IMDB Rating: {filters.imdbRatingRange[0]} - {filters.imdbRatingRange[1]}
              </Typography>
              <Slider
                value={filters.imdbRatingRange}
                onChange={(_, newValue) => handleChange('imdbRatingRange', newValue as [number, number])}
                valueLabelDisplay="auto"
                min={0}
                max={10}
                step={0.1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 5, label: '5' },
                  { value: 10, label: '10' },
                ]}
              />
            </Grid>

            {/* Runtime Range */}
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                Runtime: {filters.runtimeRange[0]} - {filters.runtimeRange[1]} minutes
              </Typography>
              <Slider
                value={filters.runtimeRange}
                onChange={(_, newValue) => handleChange('runtimeRange', newValue as [number, number])}
                valueLabelDisplay="auto"
                min={0}
                max={300}
                marks={[
                  { value: 0, label: '0m' },
                  { value: 90, label: '90m' },
                  { value: 180, label: '3h' },
                  { value: 300, label: '5h' },
                ]}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
};

export default SearchAndFilters;