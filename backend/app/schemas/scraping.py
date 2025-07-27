from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScrapingRequest(BaseModel):
    imdb_profile_url: str
    claude_api_key: Optional[str] = None

class CSVImportRequest(BaseModel):
    csv_file_path: Optional[str] = None  # If not provided, will use default path
    claude_api_key: Optional[str] = None
    scrape_posters: bool = False  # Whether to scrape poster data after import

class ScrapingStatusResponse(BaseModel):
    status: str  # "not_started", "pending", "running", "completed", "failed", "stopped"
    total_ratings: int
    scraped_ratings: int
    progress_percentage: float
    current_movie: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]