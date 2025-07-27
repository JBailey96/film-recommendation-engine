#!/usr/bin/env python3
"""
Test script to verify poster scraping functionality after CSV import.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set environment variable to use SQLite for testing
import os
os.environ["DATABASE_URL"] = "sqlite:///test_posters.db"

# Now import our modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Movie, UserRating, CastMember
from app.importer.csv_importer import CSVImporter

# Create an in-memory SQLite database for testing
engine = create_engine("sqlite:///test_posters.db", echo=False)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_poster_scraping():
    """Test poster scraping after CSV import"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Path to the CSV file
        csv_file_path = "imdb_rating.csv"
        
        if not os.path.exists(csv_file_path):
            print(f"ERROR: CSV file not found at {csv_file_path}")
            return
        
        print(f"Testing poster scraping from CSV: {csv_file_path}")
        
        # Create importer instance
        importer = CSVImporter(db, csv_file_path)
        
        # Import first 3 movies only for testing
        df = importer._read_and_validate_csv()
        if df is None:
            print("ERROR: Failed to read CSV file")
            return
        
        print(f"Importing first 3 movies for poster scraping test...")
        
        # Process first 3 rows
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            print(f"Importing movie {i+1}: {row.get('Title', 'Unknown')}")
            await importer._process_single_row(row)
        
        # Check current state
        movies = db.query(Movie).all()
        print(f"\nImported {len(movies)} movies")
        
        # Show movies without posters
        movies_without_posters = db.query(Movie).filter(Movie.poster_url.is_(None)).all()
        print(f"Movies without poster URLs: {len(movies_without_posters)}")
        
        if movies_without_posters:
            print("\nMovies needing poster data:")
            for movie in movies_without_posters:
                print(f"  - {movie.title} ({movie.year}) - IMDB: {movie.imdb_id}")
        
        # Test poster scraping (limit to 1 movie to avoid rate limiting during test)
        print(f"\nTesting poster scraping for 1 movie...")
        await importer.scrape_missing_poster_data(limit=1)
        
        # Check results
        movies_with_posters = db.query(Movie).filter(Movie.poster_url.isnot(None)).all()
        print(f"\nMovies with poster URLs after scraping: {len(movies_with_posters)}")
        
        if movies_with_posters:
            movie = movies_with_posters[0]
            print(f"\nExample movie with poster data:")
            print(f"  Title: {movie.title}")
            print(f"  Poster URL: {movie.poster_url}")
            print(f"  Plot: {movie.plot[:100] if movie.plot else 'N/A'}...")
            
            # Check cast members
            cast_count = db.query(CastMember).filter(CastMember.movie_id == movie.id).count()
            print(f"  Cast members: {cast_count}")
        
        print("\nPoster scraping test completed!")
        
    except Exception as e:
        print(f"ERROR: Error during poster scraping test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing Poster Scraping Functionality")
    print("="*50)
    asyncio.run(test_poster_scraping())