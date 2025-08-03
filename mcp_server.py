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
from app.tools import MovieTools
from sqlalchemy.orm import Session

# Initialize MCP server
server = Server("imdb-ratings-tool")


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
    tools = MovieTools(db)
    
    try:
        if uri == "movies://all":
            result = tools.filter_movies(limit=1000)  # Get all movies
            return json.dumps(result.get("movies", []), indent=2)
        
        elif uri == "movies://top-rated":
            result = tools.filter_movies(sort_by="rating", order="desc", limit=50)
            return json.dumps(result.get("movies", []), indent=2)
        
        elif uri == "movies://recent":
            result = tools.filter_movies(sort_by="rated_at", order="desc", limit=50)
            return json.dumps(result.get("movies", []), indent=2)
        
        elif uri == "cast://all":
            from app.database.models import CastMember
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
    tools = MovieTools(db)
    
    try:
        if name == "search_movies":
            result = tools.search_movies(
                query=arguments["query"],
                limit=arguments.get("limit", 10)
            )
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            movies = result.get("movies", [])
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies matching '{arguments['query']}':\n\n" + json.dumps(movies, indent=2)
            )]

        elif name == "get_movie_details":
            result = tools.get_movie_details(arguments["identifier"])
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            return [TextContent(
                type="text",
                text=f"Movie details for '{result.get('title', arguments['identifier'])}':\n\n" + json.dumps(result, indent=2)
            )]

        elif name == "get_cast_member_movies":
            result = tools.get_cast_member_movies(
                name=arguments["name"],
                role_filter=arguments.get("role_filter")
            )
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            cast_members = result.get("cast_members", [])
            response_parts = []
            for cast_data in cast_members:
                response_parts.append(f"Cast member: {cast_data['name']}\n" + json.dumps(cast_data, indent=2))
            
            return [TextContent(
                type="text",
                text=f"Found {len(cast_members)} cast member(s) matching '{arguments['name']}':\n\n" + "\n\n".join(response_parts)
            )]

        elif name == "filter_movies":
            result = tools.filter_movies(
                genres=arguments.get("genres"),
                year_min=arguments.get("year_min"),
                year_max=arguments.get("year_max"),
                user_rating_min=arguments.get("user_rating_min"),
                user_rating_max=arguments.get("user_rating_max"),
                imdb_rating_min=arguments.get("imdb_rating_min"),
                runtime_min=arguments.get("runtime_min"),
                runtime_max=arguments.get("runtime_max"),
                sort_by=arguments.get("sort_by", "rating"),
                order=arguments.get("order", "desc"),
                limit=arguments.get("limit", 20)
            )
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            movies = result.get("movies", [])
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies matching your filters:\n\n" + json.dumps(movies, indent=2)
            )]

        elif name == "get_movie_stats":
            result = tools.get_movie_stats()
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            return [TextContent(
                type="text",
                text="Movie collection statistics:\n\n" + json.dumps(result, indent=2)
            )]

        elif name == "find_similar_movies":
            result = tools.find_similar_movies(
                movie_identifier=arguments["movie_identifier"],
                similarity_type=arguments.get("similarity_type", "all"),
                limit=arguments.get("limit", 10)
            )
            
            if "error" in result:
                return [TextContent(type="text", text=result["error"])]
            
            movies = result.get("similar_movies", [])
            ref_movie = result.get("reference_movie", arguments["movie_identifier"])
            similarity_type = result.get("similarity_type", "all")
            
            return [TextContent(
                type="text",
                text=f"Found {len(movies)} movies similar to '{ref_movie}' (by {similarity_type}):\n\n" + json.dumps(movies, indent=2)
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