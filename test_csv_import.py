#!/usr/bin/env python3
"""
Simple test script to verify CSV import functionality.
This script tests the CSV importer without running the full FastAPI application.
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
os.environ["DATABASE_URL"] = "sqlite:///test.db"

# Now import our modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Movie, UserRating, CastMember
from app.importer.csv_importer import CSVImporter

# Create an in-memory SQLite database for testing
engine = create_engine("sqlite:///test.db", echo=False)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_csv_import():
    """Test the CSV import functionality"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Path to the CSV file
        csv_file_path = "imdb_rating.csv"
        
        if not os.path.exists(csv_file_path):
            print(f"ERROR: CSV file not found at {csv_file_path}")
            print("Please make sure 'imdb rating.csv' is in the current directory")
            return
        
        print(f"Testing CSV import from: {csv_file_path}")
        
        # Create importer instance
        importer = CSVImporter(db, csv_file_path)
        
        # Test CSV reading first
        df = importer._read_and_validate_csv()
        if df is None:
            print("ERROR: Failed to read CSV file")
            return
        
        print(f"CSV loaded successfully: {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head(3).to_string())
        
        # Test processing a single row
        print("\n" + "="*50)
        print("Testing single row processing...")
        
        first_row = df.iloc[0]
        print(f"Processing: {first_row.get('Title', 'Unknown')}")
        
        await importer._process_single_row(first_row)
        
        # Check what was created
        movies = db.query(Movie).all()
        ratings = db.query(UserRating).all()
        cast_members = db.query(CastMember).all()
        
        print(f"\nResults:")
        print(f"Movies created: {len(movies)}")
        print(f"Ratings created: {len(ratings)}")
        print(f"Cast members created: {len(cast_members)}")
        
        if movies:
            movie = movies[0]
            print(f"\nFirst movie details:")
            print(f"  Title: {movie.title}")
            print(f"  IMDB ID: {movie.imdb_id}")
            print(f"  Year: {movie.year}")
            print(f"  Genres: {movie.genres}")
            print(f"  Director: {movie.director}")
            print(f"  Runtime: {movie.runtime_minutes}")
            print(f"  IMDB Rating: {movie.imdb_rating}")
        
        if ratings:
            rating = ratings[0]
            print(f"\nFirst rating details:")
            print(f"  Rating: {rating.rating}")
            print(f"  Rated at: {rating.rated_at}")
        
        print("\nSingle row test completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing CSV Import Functionality")
    print("="*50)
    asyncio.run(test_csv_import())