from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from ..database.connection import get_db
from ..database.models import ScrapingStatus
from ..importer.csv_importer import CSVImporter
from ..schemas.scraping import ScrapingStatusResponse, ScrapingRequest, CSVImportRequest
import asyncio
import os

router = APIRouter()

@router.post("/start")
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start scraping IMDB ratings"""
    
    # Check if scraping is already in progress
    existing_status = db.query(ScrapingStatus).filter(
        ScrapingStatus.status.in_(["pending", "running"])
    ).first()
    
    if existing_status:
        raise HTTPException(
            status_code=400, 
            detail="Scraping is already in progress. Please wait for it to complete."
        )
    
    # Create new scraping status
    scraping_status = ScrapingStatus(
        status="pending",
        total_ratings=0,
        scraped_ratings=0
    )
    db.add(scraping_status)
    db.commit()
    
    # Start scraping in background
    
    return {"message": "Scraping started", "status_id": scraping_status.id}

@router.get("/status", response_model=ScrapingStatusResponse)
async def get_scraping_status(db: Session = Depends(get_db)):
    """Get current scraping status"""
    
    status = db.query(ScrapingStatus).order_by(ScrapingStatus.created_at.desc()).first()
    
    if not status:
        return ScrapingStatusResponse(
            status="not_started",
            total_ratings=0,
            scraped_ratings=0,
            progress_percentage=0,
            current_movie=None,
            error_message=None,
            started_at=None,
            completed_at=None
        )
    
    progress_percentage = 0
    if status.total_ratings and status.total_ratings > 0:
        progress_percentage = (status.scraped_ratings / status.total_ratings) * 100
    
    return ScrapingStatusResponse(
        status=status.status,
        total_ratings=status.total_ratings or 0,
        scraped_ratings=status.scraped_ratings or 0,
        progress_percentage=round(progress_percentage, 2),
        current_movie=status.current_movie,
        error_message=status.error_message,
        started_at=status.started_at,
        completed_at=status.completed_at
    )

@router.post("/stop")
async def stop_scraping(db: Session = Depends(get_db)):
    """Stop current scraping process"""
    
    status = db.query(ScrapingStatus).filter(
        ScrapingStatus.status.in_(["pending", "running"])
    ).first()
    
    if not status:
        raise HTTPException(status_code=400, detail="No active scraping process found")
    
    status.status = "stopped"
    status.error_message = "Stopped by user"
    db.commit()
    
    return {"message": "Scraping stopped"}

@router.delete("/reset")
async def reset_scraping_data(db: Session = Depends(get_db)):
    """Reset all scraping data and start fresh"""
    
    # Check if scraping is currently running
    active_status = db.query(ScrapingStatus).filter(
        ScrapingStatus.status.in_(["pending", "running"])
    ).first()
    
    if active_status:
        raise HTTPException(
            status_code=400, 
            detail="Cannot reset while scraping is in progress. Stop scraping first."
        )
    
    # Delete all data
    from ..database.models import Movie, UserRating, CastMember, PosterAnalysis, UserPreferences
    
    db.query(UserPreferences).delete()
    db.query(PosterAnalysis).delete()
    db.query(CastMember).delete()
    db.query(UserRating).delete()
    db.query(Movie).delete()
    db.query(ScrapingStatus).delete()
    
    db.commit()
    
    return {"message": "All data reset successfully"}

@router.post("/import-csv")
async def import_csv_data(
    request: CSVImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Import ratings data from CSV file"""
    
    # Check if import/scraping is already in progress
    existing_status = db.query(ScrapingStatus).filter(
        ScrapingStatus.status.in_(["pending", "running"])
    ).first()
    
    if existing_status:
        raise HTTPException(
            status_code=400, 
            detail="Import/scraping is already in progress. Please wait for it to complete."
        )
    
    # Determine CSV file path
    csv_file_path = request.csv_file_path
    if not csv_file_path:
        # Use default path - look for imdb rating.csv in current directory
        csv_file_path = os.path.join(os.getcwd(), "imdb_rating.csv")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        raise HTTPException(
            status_code=400,
            detail=f"CSV file not found at path: {csv_file_path}"
        )
    
    # Create new import status
    import_status = ScrapingStatus(
        status="pending",
        total_ratings=0,
        scraped_ratings=0
    )
    db.add(import_status)
    db.commit()
    
    # Start CSV import in background
    importer = CSVImporter(db, csv_file_path, request.claude_api_key)
    
    async def run_import_with_posters():
        """Run CSV import and optionally scrape posters"""
        await importer.import_csv_data()
        
        # If poster scraping is requested, do it after CSV import
        if request.scrape_posters:
            print("Starting poster data scraping...")
            await importer.scrape_missing_poster_data()
    
    background_tasks.add_task(run_import_with_posters)
    
    return {"message": "CSV import started", "status_id": import_status.id, "csv_file": csv_file_path}

@router.post("/scrape-posters")
async def scrape_missing_posters(
    background_tasks: BackgroundTasks,
    claude_api_key: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Scrape missing poster data for movies already in database"""
    
    # Check if scraping is already in progress
    existing_status = db.query(ScrapingStatus).filter(
        ScrapingStatus.status.in_(["pending", "running"])
    ).first()
    
    if existing_status:
        raise HTTPException(
            status_code=400, 
            detail="Import/scraping is already in progress. Please wait for it to complete."
        )
    
    # Create new scraping status for poster scraping
    scraping_status = ScrapingStatus(
        status="pending",
        total_ratings=0,
        scraped_ratings=0
    )
    db.add(scraping_status)
    db.commit()
    
    # Start poster scraping in background
    async def run_poster_scraping():
        """Run poster scraping with temporary importer"""
        temp_csv_path = ""  # Not needed for poster scraping
        importer = CSVImporter(db, temp_csv_path, claude_api_key)
        await importer.scrape_missing_poster_data(limit)
    
    background_tasks.add_task(run_poster_scraping)
    
    return {"message": "Poster scraping started", "status_id": scraping_status.id}