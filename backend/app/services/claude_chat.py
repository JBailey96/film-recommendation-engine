import os
import json
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database.models import ChatMessage, Movie, UserRating, CastMember

class ClaudeChatService:
    def __init__(self, db: Session):
        self.db = db
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")

    def get_system_prompt(self) -> str:
        """Generate a comprehensive system prompt for the movie assistant."""
        # Get some basic stats about the user's ratings
        total_ratings = self.db.query(UserRating).count()
        
        return f"""You are an intelligent movie assistant with access to a user's complete IMDb ratings database through MCP (Model Context Protocol) tools. The user has rated {total_ratings} movies.

Your role is to:
1. Help users explore and understand their movie preferences
2. Answer questions about their ratings, favorite actors, directors, genres, etc.
3. Provide movie recommendations based on their taste
4. Analyze viewing patterns and offer insights

IMPORTANT INSTRUCTIONS:
- You MUST use the MCP tools available to you for ALL data queries
- Available MCP tools include: search_movies, get_movie_details, get_cast_member_movies, filter_movies, get_movie_stats, find_similar_movies
- NEVER make up or guess information about the user's ratings - always use the tools to get accurate data
- When the user asks about their ratings, preferences, or movie data, immediately use the appropriate MCP tool
- Be conversational and helpful, but base all responses on actual data from the tools
- If you cannot find specific information using the tools, let the user know rather than guessing

Examples of how to help:
- "Show me my highest rated movies" → Use filter_movies with sort_by="rating" 
- "What did I rate The Matrix?" → Use search_movies then get_movie_details
- "Find movies with Tom Hanks" → Use get_cast_member_movies with name="Tom Hanks"
- "What are my favorite genres?" → Use get_movie_stats and analyze the data
- "Recommend movies like Inception" → Use find_similar_movies

Always provide context and explain your findings in a friendly, conversational way."""

    async def get_chat_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Get a response from Claude using the Anthropic API with MCP tools."""
        
        # Prepare conversation history
        messages = []
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })

        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01"
        }

        # Define MCP tools that Claude can use
        tools = [
            {
                "name": "search_movies",
                "description": "Search for movies by title, director, or cast member name",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (title, director, or cast member name)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_movie_details",
                "description": "Get detailed information about a specific movie by title or IMDb ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "Movie title or IMDb ID (e.g., 'tt0111161' or 'The Shawshank Redemption')"
                        }
                    },
                    "required": ["identifier"]
                }
            },
            {
                "name": "get_cast_member_movies",
                "description": "Get all movies featuring a specific cast member (actor, director, writer)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Full name of the cast member (e.g., 'Tom Hanks', 'Christopher Nolan')"
                        },
                        "role_filter": {
                            "type": "string",
                            "enum": ["actor", "director", "writer"],
                            "description": "Filter by role (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "filter_movies",
                "description": "Filter movies by various criteria (genre, year, rating, runtime)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "genres": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by genres (e.g., ['Action', 'Drama'])"
                        },
                        "year_min": {"type": "integer", "description": "Minimum year"},
                        "year_max": {"type": "integer", "description": "Maximum year"},
                        "imdb_rating_min": {"type": "number", "description": "Minimum IMDb rating (0-10)"},
                        "user_rating_min": {"type": "integer", "description": "Minimum user rating (1-10)"},
                        "user_rating_max": {"type": "integer", "description": "Maximum user rating (1-10)"},
                        "runtime_min": {"type": "integer", "description": "Minimum runtime in minutes"},
                        "runtime_max": {"type": "integer", "description": "Maximum runtime in minutes"},
                        "sort_by": {
                            "type": "string",
                            "enum": ["rating", "rated_at", "title", "year", "imdb_rating", "runtime_minutes"],
                            "description": "Sort results by field"
                        },
                        "order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "Sort order"
                        },
                        "limit": {"type": "integer", "description": "Maximum number of results"}
                    }
                }
            },
            {
                "name": "get_movie_stats",
                "description": "Get overall statistics about the movie collection",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "find_similar_movies",
                "description": "Find movies similar to a given movie based on genre, director, or cast",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "movie_identifier": {
                            "type": "string",
                            "description": "Movie title or IMDb ID to find similar movies for"
                        },
                        "similarity_type": {
                            "type": "string",
                            "enum": ["genre", "director", "cast", "all"],
                            "description": "Type of similarity to look for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of similar movies to return"
                        }
                    },
                    "required": ["movie_identifier"]
                }
            }
        ]

        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "system": self.get_system_prompt(),
            "messages": messages,
            "tools": tools
        }

        # Make request to Claude API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Handle tool use if present
            if result.get("content"):
                content_blocks = result["content"]
                final_response = ""
                
                for block in content_blocks:
                    if block.get("type") == "text":
                        final_response += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        # Execute the MCP tool
                        tool_name = block.get("name")
                        tool_input = block.get("input", {})
                        tool_id = block.get("id")
                        
                        try:
                            tool_result = await self.execute_mcp_tool(tool_name, tool_input)
                            
                            # Send tool result back to Claude
                            tool_result_message = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_id,
                                        "content": json.dumps(tool_result)
                                    }
                                ]
                            }
                            
                            # Make another request with the tool result
                            messages.append({
                                "role": "assistant",
                                "content": content_blocks
                            })
                            messages.append(tool_result_message)
                            
                            data["messages"] = messages
                            
                            follow_up_response = await client.post(
                                "https://api.anthropic.com/v1/messages",
                                headers=headers,
                                json=data
                            )
                            
                            if follow_up_response.status_code == 200:
                                follow_up_result = follow_up_response.json()
                                if follow_up_result.get("content"):
                                    for follow_block in follow_up_result["content"]:
                                        if follow_block.get("type") == "text":
                                            final_response += follow_block.get("text", "")
                        
                        except Exception as e:
                            final_response += f"\n\nError executing tool {tool_name}: {str(e)}"
                
                return final_response if final_response else "I apologize, but I couldn't process your request properly."
            
            return "I apologize, but I couldn't generate a response."

    async def execute_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute an MCP tool by directly calling the database functions."""
        try:
            # Import the database functions we need
            from ..database.models import Movie, UserRating, CastMember, PosterAnalysis
            from sqlalchemy import or_, and_, func, desc
            
            if tool_name == "search_movies":
                query = tool_input["query"]
                limit = tool_input.get("limit", 10)
                
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

            elif tool_name == "get_movie_details":
                identifier = tool_input["identifier"]
                
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
                
                movie_data = self._format_movie_detailed(movie, rating, cast)
                return movie_data

            elif tool_name == "filter_movies":
                # Build query with filters
                query = self.db.query(Movie, UserRating).join(UserRating)
                
                # Apply filters
                if "genres" in tool_input and tool_input["genres"]:
                    genre_conditions = [Movie.genres.contains([genre]) for genre in tool_input["genres"]]
                    query = query.filter(or_(*genre_conditions))
                
                if "year_min" in tool_input:
                    query = query.filter(Movie.year >= tool_input["year_min"])
                if "year_max" in tool_input:
                    query = query.filter(Movie.year <= tool_input["year_max"])
                
                if "user_rating_min" in tool_input:
                    query = query.filter(UserRating.rating >= tool_input["user_rating_min"])
                if "user_rating_max" in tool_input:
                    query = query.filter(UserRating.rating <= tool_input["user_rating_max"])
                
                if "imdb_rating_min" in tool_input:
                    query = query.filter(Movie.imdb_rating >= tool_input["imdb_rating_min"])
                
                # Apply sorting
                sort_by = tool_input.get("sort_by", "rating")
                order = tool_input.get("order", "desc")
                
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
                limit = tool_input.get("limit", 20)
                results = query.limit(limit).all()
                
                movies = [self._format_movie_basic(movie, rating) for movie, rating in results]
                return {"movies": movies, "count": len(movies)}

            elif tool_name == "get_movie_stats":
                stats = self.db.query(
                    func.count(UserRating.id).label("total_ratings"),
                    func.avg(UserRating.rating).label("average_rating"),
                    func.min(UserRating.rating).label("min_rating"),
                    func.max(UserRating.rating).label("max_rating"),
                    func.count(func.distinct(Movie.year)).label("unique_years"),
                    func.min(Movie.year).label("earliest_year"),
                    func.max(Movie.year).label("latest_year")
                ).join(Movie).first()
                
                stats_data = {
                    "total_ratings": int(stats.total_ratings or 0),
                    "average_rating": float(round(stats.average_rating or 0, 2)),
                    "min_rating": int(stats.min_rating or 0),
                    "max_rating": int(stats.max_rating or 0),
                    "unique_years": int(stats.unique_years or 0),
                    "earliest_year": int(stats.earliest_year or 0),
                    "latest_year": int(stats.latest_year or 0)
                }
                
                return stats_data

            elif tool_name == "get_cast_member_movies":
                name_query = tool_input["name"]
                role_filter = tool_input.get("role_filter")
                
                # Build query for cast member's movies
                cast_query = self.db.query(Movie, UserRating, CastMember).join(UserRating).join(CastMember).filter(
                    CastMember.name.ilike(f"%{name_query}%")
                )
                
                if role_filter:
                    cast_query = cast_query.filter(CastMember.role == role_filter)
                
                results = cast_query.all()
                
                if not results:
                    return {"error": f"No movies found for cast member: {name_query}"}
                
                # Group by actual cast member name
                cast_movies = {}
                for movie, rating, cast_member in results:
                    actual_name = cast_member.name
                    if actual_name not in cast_movies:
                        cast_movies[actual_name] = []
                    cast_movies[actual_name].append((movie, rating, cast_member))
                
                # Format response for each matching cast member
                cast_members_data = []
                for cast_name, movies_data in cast_movies.items():
                    movies = []
                    roles = set()
                    
                    for movie, rating, cast_member in movies_data:
                        movie_data = self._format_movie_basic(movie, rating)
                        movie_data["role_in_movie"] = cast_member.role
                        movie_data["character"] = cast_member.character
                        movies.append(movie_data)
                        roles.add(cast_member.role)
                    
                    cast_data = {
                        "name": cast_name,
                        "roles": list(roles),
                        "movie_count": len(movies),
                        "movies": movies
                    }
                    cast_members_data.append(cast_data)
                
                return {"cast_members": cast_members_data}

            elif tool_name == "find_similar_movies":
                movie_identifier = tool_input["movie_identifier"]
                similarity_type = tool_input.get("similarity_type", "all")
                limit = tool_input.get("limit", 10)
                
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
                
                # Remove duplicates and format
                seen_ids = set()
                unique_similar = []
                for movie, rating in similar_movies:
                    if movie.id not in seen_ids:
                        seen_ids.add(movie.id)
                        unique_similar.append((movie, rating))
                        if len(unique_similar) >= limit:
                            break
                
                movies = [self._format_movie_basic(movie, rating) for movie, rating in unique_similar]
                return {"similar_movies": movies, "reference_movie": ref_movie.title}

            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"error": f"Error executing tool {tool_name}: {str(e)}"}

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
                             cast: Optional[List[CastMember]] = None) -> Dict[str, Any]:
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
        
        return base_data