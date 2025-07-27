from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GenreData(BaseModel):
    genre: str
    count: int
    average_rating: float
    percentage: float

class GenreAnalysis(BaseModel):
    favorite_genres: List[GenreData]
    least_favorite_genres: List[GenreData]
    genre_distribution: Dict[str, int]
    insights: str

class YearData(BaseModel):
    year: int
    count: int
    average_rating: float

class DecadeData(BaseModel):
    decade: str
    count: int
    average_rating: float
    percentage: float

class YearAnalysis(BaseModel):
    year_distribution: List[YearData]
    decade_preferences: List[DecadeData]
    favorite_decades: List[str]
    insights: str

class RuntimeData(BaseModel):
    runtime_range: str
    count: int
    average_rating: float
    percentage: float

class RuntimeAnalysis(BaseModel):
    runtime_distribution: List[RuntimeData]
    preferred_length: str
    average_runtime: float
    insights: str

class PersonData(BaseModel):
    name: str
    count: int
    average_rating: float
    movies: List[str]

class CastAnalysis(BaseModel):
    favorite_actors: List[PersonData]
    favorite_directors: List[PersonData]
    actor_insights: str
    director_insights: str

class ColorData(BaseModel):
    color_name: str
    rgb_values: List[int]
    frequency: int
    average_rating: float

class StyleData(BaseModel):
    style: str
    count: int
    average_rating: float
    percentage: float

class PosterStyleAnalysis(BaseModel):
    dominant_colors: List[ColorData]
    style_preferences: List[StyleData]
    brightness_preference: str
    contrast_preference: str
    insights: str
    claude_analysis: Optional[str]

class OverallInsights(BaseModel):
    personality_profile: str
    viewing_patterns: str
    recommendations: List[str]
    key_preferences: Dict[str, Any]
    claude_analysis: str