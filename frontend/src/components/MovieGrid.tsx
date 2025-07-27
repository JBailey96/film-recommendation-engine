import React from 'react';
import {
  Grid,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Box,
  Chip,
  Rating,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Star as StarIcon, Info as InfoIcon } from '@mui/icons-material';
import { Rating as RatingType } from '../services/api';

interface MovieGridProps {
  ratings: RatingType[];
  onMovieClick: (rating: RatingType) => void;
  loading?: boolean;
}

const MovieGrid: React.FC<MovieGridProps> = ({ ratings, onMovieClick, loading = false }) => {
  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'success';
    if (rating >= 6) return 'warning';
    return 'error';
  };

  const formatRuntime = (minutes?: number) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <Grid container spacing={3}>
        {Array.from({ length: 12 }).map((_, index) => (
          <Grid item xs={12} sm={6} md={4} lg={3} xl={2} key={index}>
            <Card sx={{ height: 400, position: 'relative' }}>
              <Box
                sx={{
                  height: 300,
                  backgroundColor: 'grey.200',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography color="text.secondary">Loading...</Typography>
              </Box>
              <CardContent sx={{ height: 100 }}>
                <Box sx={{ backgroundColor: 'grey.100', height: 20, mb: 1 }} />
                <Box sx={{ backgroundColor: 'grey.100', height: 16, width: '60%' }} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  }

  return (
    <Grid container spacing={3}>
      {ratings.map((rating) => (
        <Grid item xs={12} sm={6} md={4} lg={3} xl={2} key={rating.movie.id}>
          <Card
            sx={{
              height: 400,
              position: 'relative',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
            onClick={() => onMovieClick(rating)}
          >
            {/* Movie Poster */}
            <Box sx={{ position: 'relative', height: 300 }}>
              {rating.movie.poster_url ? (
                <CardMedia
                  component="img"
                  height="300"
                  image={rating.movie.poster_url}
                  alt={rating.movie.title}
                  sx={{
                    objectFit: 'cover',
                    '&:hover': {
                      opacity: 0.9,
                    },
                  }}
                />
              ) : (
                <Box
                  sx={{
                    height: 300,
                    backgroundColor: 'grey.200',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'text.secondary',
                  }}
                >
                  <Typography variant="h6">No Poster</Typography>
                </Box>
              )}

              {/* User Rating Overlay */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  borderRadius: '50%',
                  width: 40,
                  height: 40,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    color: 'white',
                    fontWeight: 'bold',
                  }}
                >
                  {rating.rating}
                </Typography>
              </Box>

              {/* IMDB Rating */}
              {rating.movie.imdb_rating && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 8,
                    left: 8,
                    backgroundColor: '#f5c518',
                    borderRadius: 1,
                    px: 0.5,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                  }}
                >
                  <StarIcon sx={{ fontSize: 16, color: 'black' }} />
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'black',
                      fontWeight: 'bold',
                    }}
                  >
                    {rating.movie.imdb_rating}
                  </Typography>
                </Box>
              )}

              {/* Info Button */}
              <Tooltip title="View Details">
                <IconButton
                  sx={{
                    position: 'absolute',
                    bottom: 8,
                    right: 8,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    '&:hover': {
                      backgroundColor: 'white',
                    },
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onMovieClick(rating);
                  }}
                >
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            </Box>

            {/* Movie Info */}
            <CardContent sx={{ height: 100, p: 1.5 }}>
              <Typography
                variant="subtitle2"
                noWrap
                sx={{
                  fontWeight: 'bold',
                  mb: 0.5,
                  fontSize: '0.875rem',
                }}
                title={rating.movie.title}
              >
                {rating.movie.title}
              </Typography>

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5, gap: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {rating.movie.year}
                </Typography>
                {rating.movie.runtime_minutes && (
                  <>
                    <Typography variant="caption" color="text.secondary">
                      •
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatRuntime(rating.movie.runtime_minutes)}
                    </Typography>
                  </>
                )}
              </Box>

              {/* Genres */}
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 0.5 }}>
                {rating.movie.genres?.slice(0, 2).map((genre) => (
                  <Chip
                    key={genre}
                    label={genre}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.6rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 },
                    }}
                  />
                ))}
                {rating.movie.genres && rating.movie.genres.length > 2 && (
                  <Chip
                    label={`+${rating.movie.genres.length - 2}`}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.6rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 },
                    }}
                  />
                )}
              </Box>

              {/* Director */}
              {rating.movie.director && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  noWrap
                  sx={{ display: 'block' }}
                >
                  {rating.movie.director}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default MovieGrid;