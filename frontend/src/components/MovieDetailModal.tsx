import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Box,
  Typography,
  Chip,
  Rating,
  IconButton,
  Divider,
  Card,
  CardMedia,
} from '@mui/material';
import {
  Close as CloseIcon,
  Star as StarIcon,
  Schedule as ScheduleIcon,
  CalendarToday as CalendarIcon,
  Movie as MovieIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { Rating as RatingType } from '../services/api';

interface MovieDetailModalProps {
  open: boolean;
  onClose: () => void;
  rating: RatingType | null;
}

const MovieDetailModal: React.FC<MovieDetailModalProps> = ({ open, onClose, rating }) => {
  if (!rating) return null;

  const { movie } = rating;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatRuntime = (minutes?: number) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'success';
    if (rating >= 6) return 'warning';
    return 'error';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '80vh',
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2, display: 'flex', alignItems: 'center' }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Movie Details
        </Typography>
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Grid container spacing={3}>
          {/* Movie Poster */}
          <Grid item xs={12} md={4}>
            <Card>
              {movie.poster_url ? (
                <CardMedia
                  component="img"
                  image={movie.poster_url}
                  alt={movie.title}
                  sx={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: 500,
                    objectFit: 'cover',
                  }}
                />
              ) : (
                <Box
                  sx={{
                    height: 400,
                    backgroundColor: 'grey.200',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'text.secondary',
                  }}
                >
                  <MovieIcon sx={{ fontSize: 60 }} />
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    No Poster
                  </Typography>
                </Box>
              )}
            </Card>
          </Grid>

          {/* Movie Information */}
          <Grid item xs={12} md={8}>
            <Box>
              {/* Title */}
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
                {movie.title}
              </Typography>

              {/* Basic Info Row */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <CalendarIcon fontSize="small" color="action" />
                  <Typography variant="body2">{movie.year || 'N/A'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <ScheduleIcon fontSize="small" color="action" />
                  <Typography variant="body2">{formatRuntime(movie.runtime_minutes)}</Typography>
                </Box>
                {movie.language && (
                  <Chip label={movie.language} size="small" variant="outlined" />
                )}
                {movie.country && (
                  <Chip label={movie.country} size="small" variant="outlined" />
                )}
              </Box>

              {/* Ratings */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Ratings
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Card sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Your Rating
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mt: 1 }}>
                        <Chip
                          label={rating.rating}
                          color={getRatingColor(rating.rating) as any}
                          sx={{ fontSize: '1rem', fontWeight: 'bold' }}
                        />
                        <Rating value={rating.rating / 2} readOnly size="small" max={5} />
                      </Box>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        IMDB Rating
                      </Typography>
                      {movie.imdb_rating ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mt: 1 }}>
                          <StarIcon color="warning" />
                          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                            {movie.imdb_rating}
                          </Typography>
                          {movie.imdb_votes && (
                            <Typography variant="caption" color="text.secondary">
                              ({movie.imdb_votes.toLocaleString()} votes)
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          N/A
                        </Typography>
                      )}
                    </Card>
                  </Grid>
                </Grid>
              </Box>

              {/* Genres */}
              {movie.genres && movie.genres.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Genres
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {movie.genres.map((genre) => (
                      <Chip key={genre} label={genre} variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Director */}
              {movie.director && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Director
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color="action" />
                    <Typography variant="body1">{movie.director}</Typography>
                  </Box>
                </Box>
              )}

              {/* Plot */}
              {movie.plot && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Plot
                  </Typography>
                  <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                    {movie.plot}
                  </Typography>
                </Box>
              )}

              {/* Additional Information */}
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom>
                Additional Information
              </Typography>
              <Grid container spacing={2}>
                {movie.box_office && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Box Office
                    </Typography>
                    <Typography variant="body2">{movie.box_office}</Typography>
                  </Grid>
                )}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Date Rated
                  </Typography>
                  <Typography variant="body2">{formatDate(rating.rated_at)}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    IMDB ID
                  </Typography>
                  <Typography variant="body2">{movie.imdb_id}</Typography>
                </Grid>
              </Grid>

              {/* Review */}
              {rating.review && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Your Review
                  </Typography>
                  <Card sx={{ p: 2, backgroundColor: 'grey.50' }}>
                    <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                      "{rating.review}"
                    </Typography>
                  </Card>
                </Box>
              )}
            </Box>
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MovieDetailModal;