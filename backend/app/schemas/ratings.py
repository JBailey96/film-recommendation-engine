from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CastMemberResponse(BaseModel):
    name: str
    role: str
    character: Optional[str] = None
    
    class Config:
        from_attributes = True

class MovieResponse(BaseModel):
    id: int
    imdb_id: str
    title: str
    year: Optional[int]
    runtime_minutes: Optional[int]
    genres: Optional[List[str]]
    director: Optional[str]
    plot: Optional[str]
    poster_url: Optional[str]
    imdb_rating: Optional[float]
    imdb_votes: Optional[int]
    box_office: Optional[str]
    country: Optional[str]
    language: Optional[str]
    cast_members: Optional[List[CastMemberResponse]] = []
    
    class Config:
        from_attributes = True

class RatingResponse(BaseModel):
    movie: MovieResponse
    rating: int
    review: Optional[str]
    rated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class MovieStats(BaseModel):
    total_ratings: int
    average_rating: float
    min_rating: int
    max_rating: int
    unique_years: int
    earliest_year: int
    latest_year: int

class PaginatedRatingsResponse(BaseModel):
    ratings: List[RatingResponse]
    total: int
    skip: int
    limit: int