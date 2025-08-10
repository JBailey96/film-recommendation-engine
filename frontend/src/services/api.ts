import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface MovieStats {
  total_ratings: number;
  average_rating: number;
  min_rating: number;
  max_rating: number;
  unique_years: number;
  earliest_year: number;
  latest_year: number;
}

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

export interface ScrapingStatus {
  status: string;
  total_ratings: number;
  scraped_ratings: number;
  progress_percentage: number;
  current_movie?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface GenreData {
  genre: string;
  count: number;
  average_rating: number;
  percentage: number;
}

export interface GenreAnalysis {
  favorite_genres: GenreData[];
  least_favorite_genres: GenreData[];
  genre_distribution: Record<string, number>;
  insights: string;
}

export interface YearData {
  year: number;
  count: number;
  average_rating: number;
}

export interface DecadeData {
  decade: string;
  count: number;
  average_rating: number;
  percentage: number;
}

export interface YearAnalysis {
  year_distribution: YearData[];
  decade_preferences: DecadeData[];
  favorite_decades: string[];
  insights: string;
}

export interface RuntimeData {
  runtime_range: string;
  count: number;
  average_rating: number;
  percentage: number;
}

export interface RuntimeAnalysis {
  runtime_distribution: RuntimeData[];
  preferred_length: string;
  average_runtime: number;
  insights: string;
}

export interface PersonData {
  name: string;
  count: number;
  average_rating: number;
  movies: string[];
}

export interface CastAnalysis {
  favorite_actors: PersonData[];
  favorite_directors: PersonData[];
  actor_insights: string;
  director_insights: string;
}

export interface ColorData {
  color_name: string;
  rgb_values: number[];
  frequency: number;
  average_rating: number;
}

export interface StyleData {
  style: string;
  count: number;
  average_rating: number;
  percentage: number;
}

export interface PosterStyleAnalysis {
  dominant_colors: ColorData[];
  style_preferences: StyleData[];
  brightness_preference: string;
  contrast_preference: string;
  insights: string;
  claude_analysis?: string;
}

export interface OverallInsights {
  personality_profile: string;
  viewing_patterns: string;
  recommendations: string[];
  key_preferences: Record<string, any>;
  claude_analysis: string;
}

export interface PaginatedRatingsResponse {
  ratings: Rating[];
  total: number;
  skip: number;
  limit: number;
}

export interface RatingsSearchParams {
  skip?: number;
  limit?: number;
  sort_by?: string;
  order?: string;
  search?: string;
  genre_filter?: string;
  genres?: string[];
  year_min?: number;
  year_max?: number;
  rating_min?: number;
  rating_max?: number;
  imdb_rating_min?: number;
  imdb_rating_max?: number;
  runtime_min?: number;
  runtime_max?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistory {
  conversation_id: string;
  messages: ChatMessage[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
}

export interface SavedConversation {
  conversation_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SavedConversationsResponse {
  conversations: SavedConversation[];
}

export interface SaveConversationRequest {
  conversation_id: string;
  title: string;
}

export class ApiService {
  // Health check
  static async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await api.get('/health');
    return response.data;
  }

  // Ratings endpoints
  static async getAllRatings(params?: RatingsSearchParams): Promise<PaginatedRatingsResponse> {
    const response = await api.get('/api/ratings/', { params });
    return response.data;
  }

  static async getAvailableGenres(): Promise<string[]> {
    const response = await api.get('/api/ratings/genres');
    return response.data;
  }

  static async getRatingStats(): Promise<MovieStats> {
    const response = await api.get('/api/ratings/stats');
    return response.data;
  }

  static async getMovieRating(imdbId: string): Promise<Rating> {
    const response = await api.get(`/api/ratings/${imdbId}`);
    return response.data;
  }

  static async enrichMoviePosters(limit: number = 50): Promise<{
    message: string;
    enriched: number;
    total_processed: number;
  }> {
    const response = await api.post('/api/ratings/enrich-posters', null, {
      params: { limit }
    });
    return response.data;
  }

  // Scraping endpoints
  static async startScraping(data: {
    imdb_profile_url: string;
  }): Promise<{ message: string; status_id: number }> {
    const response = await api.post('/api/scraping/start', data);
    return response.data;
  }

  static async getScrapingStatus(): Promise<ScrapingStatus> {
    const response = await api.get('/api/scraping/status');
    return response.data;
  }

  static async stopScraping(): Promise<{ message: string }> {
    const response = await api.post('/api/scraping/stop');
    return response.data;
  }

  static async resetScrapingData(): Promise<{ message: string }> {
    const response = await api.delete('/api/scraping/reset');
    return response.data;
  }

  static async uploadCSVFile(file: File, incremental: boolean = true): Promise<{
    message: string;
    status_id: number;
    filename: string;
    incremental: boolean;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('incremental', incremental.toString());
    
    const response = await api.post('/api/scraping/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Analysis endpoints
  static async getGenreAnalysis(): Promise<GenreAnalysis> {
    const response = await api.get('/api/analysis/genres');
    return response.data;
  }

  static async getYearAnalysis(): Promise<YearAnalysis> {
    const response = await api.get('/api/analysis/years');
    return response.data;
  }

  static async getRuntimeAnalysis(): Promise<RuntimeAnalysis> {
    const response = await api.get('/api/analysis/runtime');
    return response.data;
  }

  static async getCastAnalysis(): Promise<CastAnalysis> {
    const response = await api.get('/api/analysis/cast');
    return response.data;
  }

  static async getPosterAnalysis(): Promise<PosterStyleAnalysis> {
    const response = await api.get('/api/analysis/poster-style');
    return response.data;
  }

  static async getOverallInsights(): Promise<OverallInsights> {
    const response = await api.get('/api/analysis/insights');
    return response.data;
  }

  static async regenerateAnalysis(analysisType: string): Promise<any> {
    const response = await api.post(`/api/analysis/regenerate/${analysisType}`);
    return response.data;
  }

  static async getRecommendations(limit: number = 10): Promise<any> {
    const response = await api.get('/api/analysis/recommendations', {
      params: { limit }
    });
    return response.data;
  }

  // Chat endpoints
  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/api/chat/message', request);
    return response.data;
  }

  static async getChatHistory(): Promise<ChatHistory> {
    const response = await api.get('/api/chat/history');
    return response.data;
  }

  static async clearChatHistory(): Promise<{ message: string }> {
    const response = await api.delete('/api/chat/history');
    return response.data;
  }

  static async saveConversation(request: SaveConversationRequest): Promise<{ message: string }> {
    const response = await api.post('/api/chat/conversations/save', request);
    return response.data;
  }

  static async getSavedConversations(): Promise<SavedConversationsResponse> {
    const response = await api.get('/api/chat/conversations/saved');
    return response.data;
  }

  static async getConversationById(conversationId: string): Promise<ChatHistory> {
    const response = await api.get(`/api/chat/conversations/${conversationId}`);
    return response.data;
  }

  static async deleteConversation(conversationId: string): Promise<{ message: string }> {
    const response = await api.delete(`/api/chat/conversations/${conversationId}`);
    return response.data;
  }

  static async createNewConversation(): Promise<{ conversation_id: string }> {
    const response = await api.post('/api/chat/conversations/new');
    return response.data;
  }
}