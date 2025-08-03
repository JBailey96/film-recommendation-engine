"""
Shared tool functions for movie database operations.
Used by both MCP server and Claude chat service.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

from ..database.models import Movie, UserRating, CastMember, PosterAnalysis


class MovieTools:
    """Collection of tool functions for movie database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _format_movie_basic(self, movie: Movie, rating: Optional[UserRating] = None) -> Dict[str, Any]:
        """Format movie data for basic responses"""
        return {
            "imdb_id": movie.imdb_id,
            "title": movie.title,
            "year": movie.year,
            "director": movie.director,
            "genres": movie.genres or [],
            "runtime_minutes": movie.runtime_minutes,
            "imdb_rating": float(movie.imdb_rating) if movie.imdb_rating else None,
            "user_rating": rating.rating if rating else None,
            "plot": movie.plot
        }

    def _format_movie_detailed(self, movie: Movie, rating: Optional[UserRating] = None, 
                             cast: Optional[List[CastMember]] = None,
                             poster_analysis: Optional[PosterAnalysis] = None) -> Dict[str, Any]:
        """Format movie data with all available details"""
        base_data = self._format_movie_basic(movie, rating)
        
        # Add detailed information
        base_data.update({
            "original_title": movie.original_title,
            "title_type": movie.title_type,
            "release_date": movie.release_date.isoformat() if movie.release_date else None,
            "imdb_votes": movie.imdb_votes,
            "box_office": movie.box_office,
            "country": movie.country,
            "language": movie.language,
            "poster_url": movie.poster_url,
            "rated_at": rating.rated_at.isoformat() if rating and rating.rated_at else None,
            "review": rating.review if rating else None
        })
        
        # Add cast information
        if cast:
            cast_data = {
                "actors": [{"name": c.name, "character": c.character} for c in cast if c.role == "actor"],
                "directors": [c.name for c in cast if c.role == "director"],
                "writers": [c.name for c in cast if c.role == "writer"],
                "all_cast": [{"name": c.name, "role": c.role, "character": c.character} for c in cast]
            }
            base_data["cast"] = cast_data
        
        # Add poster analysis
        if poster_analysis:
            base_data["poster_analysis"] = {
                "dominant_colors": poster_analysis.dominant_colors,
                "style_tags": poster_analysis.style_tags,
                "claude_analysis": poster_analysis.claude_analysis
            }
        
        return base_data

    def _format_cast_member_with_movies(self, name: str, movies_data: List[Tuple]) -> Dict[str, Any]:
        """Format cast member data with their movie appearances"""
        movies = []
        roles = set()
        
        for movie, rating, cast_member in movies_data:
            movie_data = self._format_movie_basic(movie, rating)
            movie_data["role_in_movie"] = cast_member.role
            movie_data["character"] = cast_member.character
            movies.append(movie_data)
            roles.add(cast_member.role)
        
        return {
            "name": name,
            "roles": list(roles),
            "movie_count": len(movies),
            "movies": movies
        }

    def search_movies(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for movies by title, director, or cast member name"""
        try:
            # Search in movies, directors, and cast
            search_filter = or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.director.ilike(f"%{query}%"),
                Movie.imdb_id.in_(
                    self.db.query(Movie.imdb_id)
                    .join(CastMember)
                    .filter(CastMember.name.ilike(f"%{query}%"))
                )
            )
            
            results = self.db.query(Movie, UserRating).join(UserRating).filter(search_filter).limit(limit).all()
            movies = [self._format_movie_basic(movie, rating) for movie, rating in results]
            
            return {"movies": movies, "count": len(movies)}
        
        except Exception as e:
            return {"error": f"Error searching movies: {str(e)}"}

    def get_movie_details(self, identifier: str) -> Dict[str, Any]:
        """Get detailed information about a specific movie by title or IMDb ID"""
        try:
            # Try to find by IMDb ID first, then by title
            if identifier.startswith("tt"):
                movie_query = self.db.query(Movie, UserRating).join(UserRating).filter(Movie.imdb_id == identifier)
            else:
                movie_query = self.db.query(Movie, UserRating).join(UserRating).filter(Movie.title.ilike(f"%{identifier}%"))
            
            result = movie_query.first()
            if not result:
                return {"error": f"Movie not found: {identifier}"}
            
            movie, rating = result
            
            # Get cast information
            cast = self.db.query(CastMember).filter(CastMember.movie_id == movie.id).all()
            
            # Get poster analysis if available
            poster_analysis = self.db.query(PosterAnalysis).filter(PosterAnalysis.movie_id == movie.id).first()
            
            movie_data = self._format_movie_detailed(movie, rating, cast, poster_analysis)
            return movie_data
        
        except Exception as e:
            return {"error": f"Error getting movie details: {str(e)}"}

    def get_cast_member_movies(self, name: str, role_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get all movies featuring a specific cast member (actor, director, writer)"""
        try:
            # Build query for cast member's movies
            cast_query = self.db.query(Movie, UserRating, CastMember).join(UserRating).join(CastMember).filter(
                CastMember.name.ilike(f"%{name}%")
            )
            
            if role_filter:
                cast_query = cast_query.filter(CastMember.role == role_filter)
            
            results = cast_query.all()
            
            if not results:
                return {"error": f"No movies found for cast member: {name}"}
            
            # Group by actual cast member name (in case of partial matches)
            cast_movies = {}
            for movie, rating, cast_member in results:
                actual_name = cast_member.name
                if actual_name not in cast_movies:
                    cast_movies[actual_name] = []
                cast_movies[actual_name].append((movie, rating, cast_member))
            
            # Format response for each matching cast member
            cast_members_data = []
            for cast_name, movies_data in cast_movies.items():
                cast_data = self._format_cast_member_with_movies(cast_name, movies_data)
                cast_members_data.append(cast_data)
            
            return {"cast_members": cast_members_data}
        
        except Exception as e:
            return {"error": f"Error getting cast member movies: {str(e)}"}

    def filter_movies(self, genres: Optional[List[str]] = None, year_min: Optional[int] = None, 
                     year_max: Optional[int] = None, user_rating_min: Optional[int] = None,
                     user_rating_max: Optional[int] = None, imdb_rating_min: Optional[float] = None,
                     runtime_min: Optional[int] = None, runtime_max: Optional[int] = None,
                     sort_by: str = "rating", order: str = "desc", limit: int = 20) -> Dict[str, Any]:
        """Filter movies by various criteria (genre, year, rating, runtime)"""
        try:
            # Build query with filters
            query = self.db.query(Movie, UserRating).join(UserRating)
            
            # Apply filters
            if genres:
                genre_conditions = [Movie.genres.contains([genre]) for genre in genres]
                query = query.filter(or_(*genre_conditions))
            
            if year_min:
                query = query.filter(Movie.year >= year_min)
            if year_max:
                query = query.filter(Movie.year <= year_max)
            
            if user_rating_min:
                query = query.filter(UserRating.rating >= user_rating_min)
            if user_rating_max:
                query = query.filter(UserRating.rating <= user_rating_max)
            
            if imdb_rating_min:
                query = query.filter(Movie.imdb_rating >= imdb_rating_min)
            
            if runtime_min:
                query = query.filter(Movie.runtime_minutes >= runtime_min)
            if runtime_max:
                query = query.filter(Movie.runtime_minutes <= runtime_max)
            
            # Apply sorting
            if sort_by == "rating":
                order_column = UserRating.rating
            elif sort_by == "rated_at":
                order_column = UserRating.rated_at
            elif sort_by == "title":
                order_column = Movie.title
            elif sort_by == "year":
                order_column = Movie.year
            elif sort_by == "imdb_rating":
                order_column = Movie.imdb_rating
            elif sort_by == "runtime_minutes":
                order_column = Movie.runtime_minutes
            else:
                order_column = UserRating.rating
            
            if order == "desc":
                order_column = order_column.desc()
            
            query = query.order_by(order_column)
            
            # Apply limit
            results = query.limit(limit).all()
            
            movies = [self._format_movie_basic(movie, rating) for movie, rating in results]
            
            return {"movies": movies, "count": len(movies)}
        
        except Exception as e:
            return {"error": f"Error filtering movies: {str(e)}"}

    def get_movie_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the movie collection"""
        try:
            stats = self.db.query(
                func.count(UserRating.id).label("total_ratings"),
                func.avg(UserRating.rating).label("average_rating"),
                func.min(UserRating.rating).label("min_rating"),
                func.max(UserRating.rating).label("max_rating"),
                func.count(func.distinct(Movie.year)).label("unique_years"),
                func.min(Movie.year).label("earliest_year"),
                func.max(Movie.year).label("latest_year")
            ).join(Movie).first()
            
            genre_count = self.db.query(func.count(func.distinct(Movie.id))).filter(Movie.genres.isnot(None)).scalar()
            cast_count = self.db.query(func.count(func.distinct(CastMember.name))).scalar()
            
            stats_data = {
                "total_ratings": int(stats.total_ratings or 0),
                "average_rating": float(round(stats.average_rating or 0, 2)),
                "min_rating": int(stats.min_rating or 0),
                "max_rating": int(stats.max_rating or 0),
                "unique_years": int(stats.unique_years or 0),
                "earliest_year": int(stats.earliest_year or 0),
                "latest_year": int(stats.latest_year or 0),
                "movies_with_genres": int(genre_count or 0),
                "unique_cast_members": int(cast_count or 0)
            }
            
            return stats_data
        
        except Exception as e:
            return {"error": f"Error getting movie stats: {str(e)}"}

    def find_similar_movies(self, movie_identifier: str, similarity_type: str = "all", 
                          limit: int = 10) -> Dict[str, Any]:
        """Find movies similar to a given movie based on genre, director, or cast"""
        try:
            # Find the reference movie
            if movie_identifier.startswith("tt"):
                ref_movie = self.db.query(Movie).filter(Movie.imdb_id == movie_identifier).first()
            else:
                ref_movie = self.db.query(Movie).filter(Movie.title.ilike(f"%{movie_identifier}%")).first()
            
            if not ref_movie:
                return {"error": f"Reference movie not found: {movie_identifier}"}
            
            similar_movies = []
            
            if similarity_type in ["genre", "all"] and ref_movie.genres:
                # Find movies with similar genres
                genre_conditions = [Movie.genres.contains([genre]) for genre in ref_movie.genres]
                genre_similar = self.db.query(Movie, UserRating).join(UserRating).filter(
                    and_(Movie.id != ref_movie.id, or_(*genre_conditions))
                ).limit(limit).all()
                similar_movies.extend(genre_similar)
            
            if similarity_type in ["director", "all"] and ref_movie.director:
                # Find movies by the same director
                director_similar = self.db.query(Movie, UserRating).join(UserRating).filter(
                    and_(Movie.id != ref_movie.id, Movie.director == ref_movie.director)
                ).limit(limit).all()
                similar_movies.extend(director_similar)
            
            if similarity_type in ["cast", "all"]:
                # Find movies with shared cast members
                ref_cast = self.db.query(CastMember.name).filter(CastMember.movie_id == ref_movie.id).subquery()
                cast_similar = self.db.query(Movie, UserRating).join(UserRating).join(CastMember).filter(
                    and_(Movie.id != ref_movie.id, CastMember.name.in_(ref_cast))
                ).limit(limit).all()
                similar_movies.extend(cast_similar)
            
            # Remove duplicates and limit results
            seen_ids = set()
            unique_similar = []
            for movie, rating in similar_movies:
                if movie.id not in seen_ids:
                    seen_ids.add(movie.id)
                    unique_similar.append((movie, rating))
                    if len(unique_similar) >= limit:
                        break
            
            movies = [self._format_movie_basic(movie, rating) for movie, rating in unique_similar]
            
            return {
                "similar_movies": movies, 
                "reference_movie": ref_movie.title,
                "similarity_type": similarity_type,
                "count": len(movies)
            }
        
        except Exception as e:
            return {"error": f"Error finding similar movies: {str(e)}"}