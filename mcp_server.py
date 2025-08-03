#!/usr/bin/env python3
"""
MCP Server for IMDb Ratings Database
Provides comprehensive movie data access for AI assistants.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from mcp.server.models import InitializationOptions
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource

from app.database.connection import get_db
from app.database.models import Movie, UserRating, CastMember, PosterAnalysis
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

# Initialize MCP server
server = Server("imdb-ratings-tool")

def format_movie_basic(movie: Movie, rating: Optional[UserRating] = None) -> Dict[str, Any]:
    """Format movie data for basic responses"""
    return {
        "imdb_id": movie.imdb_id,
        "title": movie.title,
        "year": movie.year,
        "director": movie.director,
        "genres": movie.genres or [],
        "runtime_minutes": movie.runtime_minutes,
        "imdb_rating": movie.imdb_rating,
        "user_rating": rating.rating if rating else None,
        "plot": movie.plot
    }

def format_movie_detailed(movie: Movie, rating: Optional[UserRating] = None, 
                         cast: Optional[List[CastMember]] = None,
                         poster_analysis: Optional[PosterAnalysis] = None) -> Dict[str, Any]:
    """Format movie data with all available details"""
    base_data = format_movie_basic(movie, rating)
    
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

def format_cast_member_with_movies(name: str, movies_data: List[tuple]) -> Dict[str, Any]:
    """Format cast member data with their movie appearances"""
    movies = []
    roles = set()
    
    for movie, rating, cast_member in movies_data:
        movie_data = format_movie_basic(movie, rating)
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

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available movie database resources"""
    return [
        Resource(
            uri="movies://all",
            name="All Movies",
            description="Complete list of all movies in the database",
            mimeType="application/json"
        ),
        Resource(
            uri="movies://top-rated",
            name="Top Rated Movies",
            description="Movies sorted by user rating (highest first)",
            mimeType="application/json"
        ),
        Resource(
            uri="movies://recent",
            name="Recently Rated Movies",
            description="Movies sorted by rating date (most recent first)",
            mimeType="application/json"
        ),
        Resource(
            uri="cast://all",
            name="All Cast Members",
            description="Complete list of all cast members in the database",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read movie database resources"""
    db = next(get_db())
    
    try:
        if uri == "movies://all":
            results = db.query(Movie, UserRating).join(UserRating).all()
            movies = [format_movie_basic(movie, rating) for movie, rating in results]
            return json.dumps(movies, indent=2)
        
        elif uri == "movies://top-rated":
            results = db.query(Movie, UserRating).join(UserRating).order_by(desc(UserRating.rating)).limit(50).all()
            movies = [format_movie_basic(movie, rating) for movie, rating in results]
            return json.dumps(movies, indent=2)
        
        elif uri == "movies://recent":
            results = db.query(Movie, UserRating).join(UserRating).order_by(desc(UserRating.rated_at)).limit(50).all()
            movies = [format_movie_basic(movie, rating) for movie, rating in results]
            return json.dumps(movies, indent=2)
        
        elif uri == "cast://all":
            cast_members = db.query(CastMember.name).distinct().all()
            names = [member.name for member in cast_members]
            return json.dumps(sorted(names), indent=2)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    finally:
        db.close()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available movie database tools"""
    return [
        Tool(
            name="search_movies",
            description="Search for movies by title, director, or cast member name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (title, director, or cast member name)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_movie_details",
            description="Get detailed information about a specific movie by title or IMDb ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Movie title or IMDb ID (e.g., 'tt0111161' or 'The Shawshank Redemption')"
                    }
                },
                "required": ["identifier"]
            }
        ),
        Tool(
            name="get_cast_member_movies",
            description="Get all movies featuring a specific cast member (actor, director, writer)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the cast member (e.g., 'Tom Hanks', 'Christopher Nolan')"
                    },
                    "role_filter": {
                        "type": "string",
                        "description": "Filter by role: 'actor', 'director', 'writer' (optional)",
                        "enum": ["actor", "director", "writer"]
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="filter_movies",
            description="Filter movies by various criteria (genre, year, rating, runtime)",
            inputSchema={
                "type": "object",
                "properties": {
                    "genres": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by genres (e.g., ['Action', 'Drama'])"
                    },
                    "year_min": {
                        "type": "integer",
                        "description": "Minimum year"
                    },
                    "year_max": {
                        "type": "integer", 
                        "description": "Maximum year"
                    },
                    "user_rating_min": {
                        "type": "integer",
                        "description": "Minimum user rating (1-10)"
                    },
                    "user_rating_max": {
                        "type": "integer",
                        "description": "Maximum user rating (1-10)"
                    },
                    "imdb_rating_min": {
                        "type": "number",
                        "description": "Minimum IMDb rating (0-10)"
                    },
                    "runtime_min": {
                        "type": "integer",
                        "description": "Minimum runtime in minutes"
                    },
                    "runtime_max": {
                        "type": "integer",
                        "description": "Maximum runtime in minutes"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["rating", "rated_at", "title", "year", "imdb_rating", "runtime_minutes"],
                        "description": "Sort results by field",
                        "default": "rating"
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort order",
                        "default": "desc"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="get_movie_stats",
            description="Get overall statistics about the movie collection",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="find_similar_movies",
            description="Find movies similar to a given movie based on genre, director, or cast",
            inputSchema={
                "type": "object",
                "properties": {
                    "movie_identifier": {
                        "type": "string",
                        "description": "Movie title or IMDb ID to find similar movies for"
                    },
                    "similarity_type": {
                        "type": "string",
                        "enum": ["genre", "director", "cast", "all"],
                        "description": "Type of similarity to look for",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of similar movies to return",
                        "default": 10
                    }
                },
                "required": ["movie_identifier"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for movie database operations"""
    db = next(get_db())
    
    try:
        if name == "search_movies":
            query = arguments["query"]
            limit = arguments.get("limit", 10)
            
            # Search in movies, directors, and cast
            search_filter = or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.director.ilike(f"%{query}%"),
                Movie.imdb_id.in_(
                    db.query(Movie.imdb_id)
                    .join(CastMember)
                    .filter(CastMember.name.ilike(f"%{query}%"))
                )
            )
            
            results = db.query(Movie, UserRating).join(UserRating).filter(search_filter).limit(limit).all()
            movies = [format_movie_basic(movie, rating) for movie, rating in results]
            
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies matching '{query}':\n\n" + json.dumps(movies, indent=2)
            )]

        elif name == "get_movie_details":
            identifier = arguments["identifier"]
            
            # Try to find by IMDb ID first, then by title
            if identifier.startswith("tt"):
                movie_query = db.query(Movie, UserRating).join(UserRating).filter(Movie.imdb_id == identifier)
            else:
                movie_query = db.query(Movie, UserRating).join(UserRating).filter(Movie.title.ilike(f"%{identifier}%"))
            
            result = movie_query.first()
            if not result:
                return [TextContent(type="text", text=f"Movie not found: {identifier}")]
            
            movie, rating = result
            
            # Get cast information
            cast = db.query(CastMember).filter(CastMember.movie_id == movie.id).all()
            
            # Get poster analysis if available
            poster_analysis = db.query(PosterAnalysis).filter(PosterAnalysis.movie_id == movie.id).first()
            
            movie_data = format_movie_detailed(movie, rating, cast, poster_analysis)
            
            return [TextContent(
                type="text",
                text=f"Movie details for '{movie.title}':\n\n" + json.dumps(movie_data, indent=2)
            )]

        elif name == "get_cast_member_movies":
            name_query = arguments["name"]
            role_filter = arguments.get("role_filter")
            
            # Build query for cast member's movies
            cast_query = db.query(Movie, UserRating, CastMember).join(UserRating).join(CastMember).filter(
                CastMember.name.ilike(f"%{name_query}%")
            )
            
            if role_filter:
                cast_query = cast_query.filter(CastMember.role == role_filter)
            
            results = cast_query.all()
            
            if not results:
                return [TextContent(type="text", text=f"No movies found for cast member: {name_query}")]
            
            # Group by actual cast member name (in case of partial matches)
            cast_movies = {}
            for movie, rating, cast_member in results:
                actual_name = cast_member.name
                if actual_name not in cast_movies:
                    cast_movies[actual_name] = []
                cast_movies[actual_name].append((movie, rating, cast_member))
            
            # Format response for each matching cast member
            response_parts = []
            for cast_name, movies_data in cast_movies.items():
                cast_data = format_cast_member_with_movies(cast_name, movies_data)
                response_parts.append(f"Cast member: {cast_name}\n" + json.dumps(cast_data, indent=2))
            
            return [TextContent(
                type="text",
                text=f"Found {len(cast_movies)} cast member(s) matching '{name_query}':\n\n" + "\n\n".join(response_parts)
            )]

        elif name == "filter_movies":
            # Build query with filters
            query = db.query(Movie, UserRating).join(UserRating)
            
            # Apply filters
            if "genres" in arguments and arguments["genres"]:
                genre_conditions = [Movie.genres.contains([genre]) for genre in arguments["genres"]]
                query = query.filter(or_(*genre_conditions))
            
            if "year_min" in arguments:
                query = query.filter(Movie.year >= arguments["year_min"])
            if "year_max" in arguments:
                query = query.filter(Movie.year <= arguments["year_max"])
            
            if "user_rating_min" in arguments:
                query = query.filter(UserRating.rating >= arguments["user_rating_min"])
            if "user_rating_max" in arguments:
                query = query.filter(UserRating.rating <= arguments["user_rating_max"])
            
            if "imdb_rating_min" in arguments:
                query = query.filter(Movie.imdb_rating >= arguments["imdb_rating_min"])
            
            if "runtime_min" in arguments:
                query = query.filter(Movie.runtime_minutes >= arguments["runtime_min"])
            if "runtime_max" in arguments:
                query = query.filter(Movie.runtime_minutes <= arguments["runtime_max"])
            
            # Apply sorting
            sort_by = arguments.get("sort_by", "rating")
            order = arguments.get("order", "desc")
            
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
            
            if order == "desc":
                order_column = order_column.desc()
            
            query = query.order_by(order_column)
            
            # Apply limit
            limit = arguments.get("limit", 20)
            results = query.limit(limit).all()
            
            movies = [format_movie_basic(movie, rating) for movie, rating in results]
            
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies matching your filters:\n\n" + json.dumps(movies, indent=2)
            )]

        elif name == "get_movie_stats":
            stats = db.query(
                func.count(UserRating.id).label("total_ratings"),
                func.avg(UserRating.rating).label("average_rating"),
                func.min(UserRating.rating).label("min_rating"),
                func.max(UserRating.rating).label("max_rating"),
                func.count(func.distinct(Movie.year)).label("unique_years"),
                func.min(Movie.year).label("earliest_year"),
                func.max(Movie.year).label("latest_year")
            ).join(Movie).first()
            
            genre_count = db.query(func.count(func.distinct(Movie.id))).filter(Movie.genres.isnot(None)).scalar()
            cast_count = db.query(func.count(func.distinct(CastMember.name))).scalar()
            
            stats_data = {
                "total_ratings": stats.total_ratings or 0,
                "average_rating": round(stats.average_rating or 0, 2),
                "min_rating": stats.min_rating or 0,
                "max_rating": stats.max_rating or 0,
                "unique_years": stats.unique_years or 0,
                "earliest_year": stats.earliest_year or 0,
                "latest_year": stats.latest_year or 0,
                "movies_with_genres": genre_count or 0,
                "unique_cast_members": cast_count or 0
            }
            
            return [TextContent(
                type="text",
                text="Movie collection statistics:\n\n" + json.dumps(stats_data, indent=2)
            )]

        elif name == "find_similar_movies":
            movie_identifier = arguments["movie_identifier"]
            similarity_type = arguments.get("similarity_type", "all")
            limit = arguments.get("limit", 10)
            
            # Find the reference movie
            if movie_identifier.startswith("tt"):
                ref_movie = db.query(Movie).filter(Movie.imdb_id == movie_identifier).first()
            else:
                ref_movie = db.query(Movie).filter(Movie.title.ilike(f"%{movie_identifier}%")).first()
            
            if not ref_movie:
                return [TextContent(type="text", text=f"Reference movie not found: {movie_identifier}")]
            
            similar_movies = []
            
            if similarity_type in ["genre", "all"]:
                # Find movies with similar genres
                if ref_movie.genres:
                    genre_conditions = [Movie.genres.contains([genre]) for genre in ref_movie.genres]
                    genre_similar = db.query(Movie, UserRating).join(UserRating).filter(
                        and_(Movie.id != ref_movie.id, or_(*genre_conditions))
                    ).limit(limit).all()
                    similar_movies.extend(genre_similar)
            
            if similarity_type in ["director", "all"]:
                # Find movies by the same director
                if ref_movie.director:
                    director_similar = db.query(Movie, UserRating).join(UserRating).filter(
                        and_(Movie.id != ref_movie.id, Movie.director == ref_movie.director)
                    ).limit(limit).all()
                    similar_movies.extend(director_similar)
            
            if similarity_type in ["cast", "all"]:
                # Find movies with shared cast members
                ref_cast = db.query(CastMember.name).filter(CastMember.movie_id == ref_movie.id).subquery()
                cast_similar = db.query(Movie, UserRating).join(UserRating).join(CastMember).filter(
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
            
            movies = [format_movie_basic(movie, rating) for movie, rating in unique_similar]
            
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies similar to '{ref_movie.title}' (by {similarity_type}):\n\n" + json.dumps(movies, indent=2)
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    finally:
        db.close()

async def main():
    """Run the MCP server"""
    # Verify database connection
    try:
        db = next(get_db())
        db.close()
        print("Database connection verified", file=sys.stderr)
    except Exception as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="imdb-ratings-tool",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())