"""
TMDb (The Movie Database) API service for fetching movie posters and metadata.
Free API service for non-commercial use with proper attribution.
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class TMDbService:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('TMDB_API_KEY')
        if not self.api_key:
            logger.warning("TMDb API key not provided. Poster fetching will be disabled.")
    
    async def find_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict[Any, Any]]:
        """Find a movie using its IMDb ID."""
        if not self.api_key:
            return None
            
        url = f"{self.BASE_URL}/find/{imdb_id}"
        params = {
            'api_key': self.api_key,
            'external_source': 'imdb_id'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('movie_results'):
                            return data['movie_results'][0]
                    else:
                        logger.warning(f"TMDb API error for {imdb_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching movie data for {imdb_id}: {e}")
            return None
    
    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[Any, Any]]:
        """Get detailed movie information including cast and crew."""
        if not self.api_key:
            return None
            
        url = f"{self.BASE_URL}/movie/{tmdb_id}"
        params = {
            'api_key': self.api_key,
            'append_to_response': 'credits,images'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"TMDb API error for movie {tmdb_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching movie details for {tmdb_id}: {e}")
            return None
    
    def get_poster_url(self, poster_path: str, size: str = "w500") -> str:
        """
        Generate full poster URL from TMDb poster path.
        
        Available sizes: w92, w154, w185, w342, w500, w780, original
        """
        if not poster_path:
            return ""
        return f"{self.IMAGE_BASE_URL}/{size}{poster_path}"
    
    def get_backdrop_url(self, backdrop_path: str, size: str = "w1280") -> str:
        """
        Generate full backdrop URL from TMDb backdrop path.
        
        Available sizes: w300, w780, w1280, original
        """
        if not backdrop_path:
            return ""
        return f"{self.IMAGE_BASE_URL}/{size}{backdrop_path}"
    
    async def enrich_movie_data(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Enrich movie data using TMDb API.
        Returns dictionary with poster_url and other enhanced data.
        """
        if not self.api_key:
            return None
            
        try:
            # Find movie by IMDb ID
            movie_data = await self.find_movie_by_imdb_id(imdb_id)
            if not movie_data:
                return None
            
            # Get detailed information
            tmdb_id = movie_data['id']
            details = await self.get_movie_details(tmdb_id)
            if not details:
                return None
            
            # Extract relevant data
            enriched_data = {}
            
            # Poster URL (high quality)
            if details.get('poster_path'):
                enriched_data['poster_url'] = self.get_poster_url(details['poster_path'], 'w500')
            
            # Backdrop URL
            if details.get('backdrop_path'):
                enriched_data['backdrop_url'] = self.get_backdrop_url(details['backdrop_path'])
            
            # Enhanced plot/overview
            if details.get('overview') and len(details['overview']) > 50:
                enriched_data['plot'] = details['overview']
            
            # Additional metadata
            if details.get('tagline'):
                enriched_data['tagline'] = details['tagline']
            
            # Budget and revenue
            if details.get('budget') and details['budget'] > 0:
                enriched_data['budget'] = details['budget']
            
            if details.get('revenue') and details['revenue'] > 0:
                enriched_data['revenue'] = details['revenue']
            
            # Production countries
            if details.get('production_countries'):
                countries = [country['name'] for country in details['production_countries']]
                if countries:
                    enriched_data['production_countries'] = countries
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching movie data for {imdb_id}: {e}")
            return None
    
    async def batch_enrich_movies(self, movie_imdb_ids: list, delay: float = 0.1) -> Dict[str, Dict]:
        """
        Batch process multiple movies with rate limiting.
        Returns dictionary mapping IMDb ID to enriched data.
        """
        results = {}
        
        for i, imdb_id in enumerate(movie_imdb_ids):
            try:
                enriched = await self.enrich_movie_data(imdb_id)
                if enriched:
                    results[imdb_id] = enriched
                
                # Rate limiting - TMDb allows 40 requests per 10 seconds
                if i < len(movie_imdb_ids) - 1:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error in batch processing for {imdb_id}: {e}")
                continue
        
        return results