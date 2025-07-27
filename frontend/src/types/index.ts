export interface Movie {
  id: number;
  imdb_id: string;
  title: string;
  year?: number;
  runtime_minutes?: number;
  genres?: string[];
  director?: string;
  plot?: string;
  poster_url?: string;
  imdb_rating?: number;
  imdb_votes?: number;
  box_office?: string;
  country?: string;
  language?: string;
}

export interface Rating {
  movie: Movie;
  rating: number;
  review?: string;
  rated_at?: string;
}

export interface MovieStats {
  total_ratings: number;
  average_rating: number;
  min_rating: number;
  max_rating: number;
  unique_years: number;
  earliest_year: number;
  latest_year: number;
}

export interface ScrapingStatus {
  status: 'not_started' | 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  total_ratings: number;
  scraped_ratings: number;
  progress_percentage: number;
  current_movie?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface ChartData {
  name: string;
  value: number;
  count?: number;
  rating?: number;
}