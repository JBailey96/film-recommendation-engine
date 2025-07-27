import pandas as pd
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import re
from pathlib import Path

from ..database.models import Movie, UserRating, CastMember, ScrapingStatus
from ..analysis.poster_analyzer import PosterAnalyzer


class CSVImporter:
    def __init__(self, db: Session, csv_file_path: str, claude_api_key: Optional[str] = None):
        self.db = db
        self.csv_file_path = csv_file_path
        self.claude_api_key = claude_api_key
        
    def _update_import_status(self, status: str, **kwargs):
        """Update import status in database using scraping_status table"""
        import_status = self.db.query(ScrapingStatus).order_by(ScrapingStatus.created_at.desc()).first()
        if import_status:
            import_status.status = status
            for key, value in kwargs.items():
                if hasattr(import_status, key):
                    setattr(import_status, key, value)
            self.db.commit()
    
    async def import_csv_data(self):
        """Main method to import all data from CSV"""
        try:
            self._update_import_status("running", started_at=datetime.utcnow())
            
            # Read and validate CSV
            df = self._read_and_validate_csv()
            if df is None:
                return
            
            total_ratings = len(df)
            self._update_import_status("running", total_ratings=total_ratings)
            
            # Process each row
            for i, row in df.iterrows():
                await self._process_single_row(row)
                self._update_import_status("running", 
                                         scraped_ratings=i+1,
                                         current_movie=row.get('Title', ''))
            
            self._update_import_status("completed", completed_at=datetime.utcnow())
            print(f"Successfully imported {total_ratings} ratings from CSV")
            
        except Exception as e:
            error_msg = str(e)
            print(f"CSV import failed: {error_msg}")
            self._update_import_status("failed", error_message=error_msg)
    
    def _read_and_validate_csv(self) -> Optional[pd.DataFrame]:
        """Read and validate the CSV file"""
        try:
            if not Path(self.csv_file_path).exists():
                raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
            
            # Read CSV
            df = pd.read_csv(self.csv_file_path)
            
            # Validate required columns
            required_columns = ['Const', 'Your Rating', 'Title', 'Year']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            print(f"CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            print(f"Error reading CSV: {e}")
            self._update_import_status("failed", error_message=f"Error reading CSV: {e}")
            return None
    
    async def _process_single_row(self, row):
        """Process and save a single CSV row"""
        try:
            # Extract IMDB ID
            imdb_id = str(row['Const']).strip()
            if not imdb_id.startswith('tt'):
                print(f"Invalid IMDB ID: {imdb_id}")
                return
            
            # Check if movie already exists
            existing_movie = self.db.query(Movie).filter(Movie.imdb_id == imdb_id).first()
            
            if not existing_movie:
                # Create new movie record
                movie_data = self._extract_movie_data(row)
                movie = Movie(**movie_data)
                self.db.add(movie)
                self.db.flush()  # Get the ID
                
                # Add director as cast member if present
                director = self._clean_text_field(row.get('Directors'))
                if director:
                    # Handle multiple directors separated by commas
                    directors = [d.strip() for d in director.split(',')]
                    for dir_name in directors[:3]:  # Limit to first 3 directors
                        if dir_name:
                            cast_record = CastMember(
                                movie_id=movie.id,
                                name=dir_name,
                                role='director'
                            )
                            self.db.add(cast_record)
            else:
                movie = existing_movie
            
            # Check if user rating already exists
            existing_rating = self.db.query(UserRating).filter(UserRating.movie_id == movie.id).first()
            
            if not existing_rating:
                # Create user rating record
                rating_data = self._extract_rating_data(row)
                rating_data['movie_id'] = movie.id
                user_rating = UserRating(**rating_data)
                self.db.add(user_rating)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error processing row for {row.get('Title', 'Unknown')}: {e}")
            self.db.rollback()
    
    def _extract_movie_data(self, row) -> Dict:
        """Extract movie data from CSV row"""
        data = {}
        
        # Basic fields
        data['imdb_id'] = str(row['Const']).strip()
        data['title'] = self._clean_text_field(row.get('Title'))
        data['original_title'] = self._clean_text_field(row.get('Original Title'))
        data['title_type'] = self._clean_text_field(row.get('Title Type'))
        
        # Year
        year = row.get('Year')
        if pd.notna(year):
            try:
                data['year'] = int(year)
            except (ValueError, TypeError):
                pass
        
        # Release Date
        release_date = row.get('Release Date')
        if pd.notna(release_date):
            try:
                data['release_date'] = pd.to_datetime(release_date).to_pydatetime()
            except (ValueError, TypeError):
                pass
        
        # Runtime
        runtime = row.get('Runtime (mins)')
        if pd.notna(runtime):
            try:
                data['runtime_minutes'] = int(runtime)
            except (ValueError, TypeError):
                pass
        
        # IMDB Rating
        imdb_rating = row.get('IMDb Rating')
        if pd.notna(imdb_rating):
            try:
                data['imdb_rating'] = float(imdb_rating)
            except (ValueError, TypeError):
                pass
        
        # IMDB Votes
        num_votes = row.get('Num Votes')
        if pd.notna(num_votes):
            try:
                # Remove commas from vote counts
                votes_str = str(num_votes).replace(',', '')
                data['imdb_votes'] = int(votes_str)
            except (ValueError, TypeError):
                pass
        
        # Genres - parse comma-separated list
        genres = self._clean_text_field(row.get('Genres'))
        if genres:
            # Split by comma and clean each genre
            genre_list = [g.strip() for g in genres.split(',') if g.strip()]
            data['genres'] = genre_list
        
        # Director (primary director only for movie table)
        directors = self._clean_text_field(row.get('Directors'))
        if directors:
            # Take first director for movie.director field
            first_director = directors.split(',')[0].strip()
            data['director'] = first_director
        
        # Construct poster URL from IMDB ID (we'll update this later with actual URLs)
        data['poster_url'] = None
        
        return data
    
    def _extract_rating_data(self, row) -> Dict:
        """Extract user rating data from CSV row"""
        data = {}
        
        # User rating
        rating = row.get('Your Rating')
        if pd.notna(rating):
            try:
                data['rating'] = int(rating)
            except (ValueError, TypeError):
                print(f"Invalid rating value: {rating}")
                return {}
        
        # Rating date
        date_rated = row.get('Date Rated')
        if pd.notna(date_rated):
            try:
                # Parse date string (assuming YYYY-MM-DD format from CSV)
                data['rated_at'] = pd.to_datetime(date_rated).to_pydatetime()
            except (ValueError, TypeError):
                print(f"Invalid date format: {date_rated}")
        
        return data
    
    def _clean_text_field(self, value) -> Optional[str]:
        """Clean and validate text fields"""
        if pd.isna(value) or value is None:
            return None
        
        text = str(value).strip()
        return text if text else None
    
    async def scrape_missing_poster_data(self, limit: Optional[int] = None):
        # """Scrape poster URLs and other missing data for movies imported from CSV"""
        # try:
        #     # Find movies without poster URLs
        #     query = self.db.query(Movie).filter(Movie.poster_url.is_(None))
        #     if limit:
        #         query = query.limit(limit)
            
        #     movies_without_posters = query.all()
        #     print(f"Found {len(movies_without_posters)} movies without poster data")
            
        #     if not movies_without_posters:
        #         return
            
        #     # Import scraper for individual movie details
        #     from ..scraper.imdb_scraper import IMDBScraper
            
        #     # Create temporary scraper instance
        #     dummy_profile_url = "https://www.imdb.com/user/ur0000001"  # Dummy URL
        #     scraper = IMDBScraper(self.db, dummy_profile_url, self.claude_api_key)
            
        #     for i, movie in enumerate(movies_without_posters):
        #         try:
        #             print(f"Scraping poster data for {movie.title} ({i+1}/{len(movies_without_posters)})")
                    
        #             # Construct IMDB URL
        #             movie_url = f"https://www.imdb.com/title/{movie.imdb_id}/"
                    
        #             # Scrape movie details (this will get poster URL and other missing data)
        #             movie_details = await scraper._scrape_movie_details(movie_url)
                    
        #             # Update movie with new data
        #             if movie_details.get('poster_url'):
        #                 movie.poster_url = movie_details['poster_url']
                    
        #             # Update other fields if they're missing
        #             if not movie.plot and movie_details.get('plot'):
        #                 movie.plot = movie_details['plot']
                    
        #             # Add cast members if not present
        #             if movie_details.get('cast') and not movie.cast_members:
        #                 for cast_member in movie_details['cast'][:10]:  # Limit to 10
        #                     cast_record = CastMember(
        #                         movie_id=movie.id,
        #                         name=cast_member['name'],
        #                         role=cast_member['role'],
        #                         character=cast_member.get('character')
        #                     )
        print("Poster scraping is disabled: IMDBScraper has been removed.")
        return