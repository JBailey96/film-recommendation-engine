import os
import json
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database.models import ChatMessage, UserRating
from ..tools import MovieTools

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
            
            # Handle tool use if present - support multiple rounds of tool calls
            max_iterations = 5  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations and result.get("content"):
                content_blocks = result["content"]
                text_response = ""
                tool_calls = []
                
                # Process all content blocks
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_response += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append(block)
                
                # If there are no tool calls, we're done
                if not tool_calls:
                    return text_response if text_response else "I apologize, but I couldn't generate a response."
                
                # Execute all tool calls
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_input = tool_call.get("input", {})
                    tool_id = tool_call.get("id")
                    
                    try:
                        tool_result = await self.execute_mcp_tool(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(tool_result)
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps({"error": f"Error executing tool {tool_name}: {str(e)}"})
                        })
                
                # Send all tool results back to Claude
                messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Make another request with all tool results
                data["messages"] = messages
                
                follow_up_response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data
                )
                
                if follow_up_response.status_code == 200:
                    result = follow_up_response.json()
                    iteration += 1
                else:
                    return f"Error in follow-up request: {follow_up_response.status_code} - {follow_up_response.text}"
            
            # After the loop, extract final text response
            if result.get("content"):
                final_response = ""
                for block in result["content"]:
                    if block.get("type") == "text":
                        final_response += block.get("text", "")
                return final_response if final_response else "I apologize, but I couldn't process your request properly."
            
            return "I apologize, but I couldn't generate a response."

    async def execute_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute an MCP tool using the shared MovieTools functions."""
        try:
            # Use a fresh database session for tool execution to avoid transaction conflicts
            from ..database.connection import get_db
            tool_db = next(get_db())
            tools = MovieTools(tool_db)
            
            if tool_name == "search_movies":
                return tools.search_movies(
                    query=tool_input["query"],
                    limit=tool_input.get("limit", 10)
                )
            
            elif tool_name == "get_movie_details":
                return tools.get_movie_details(tool_input["identifier"])
            
            elif tool_name == "filter_movies":
                return tools.filter_movies(
                    genres=tool_input.get("genres"),
                    year_min=tool_input.get("year_min"),
                    year_max=tool_input.get("year_max"),
                    user_rating_min=tool_input.get("user_rating_min"),
                    user_rating_max=tool_input.get("user_rating_max"),
                    imdb_rating_min=tool_input.get("imdb_rating_min"),
                    runtime_min=tool_input.get("runtime_min"),
                    runtime_max=tool_input.get("runtime_max"),
                    sort_by=tool_input.get("sort_by", "rating"),
                    order=tool_input.get("order", "desc"),
                    limit=tool_input.get("limit", 20)
                )
            
            elif tool_name == "get_movie_stats":
                return tools.get_movie_stats()
            
            elif tool_name == "get_cast_member_movies":
                return tools.get_cast_member_movies(
                    name=tool_input["name"],
                    role_filter=tool_input.get("role_filter")
                )
            
            elif tool_name == "find_similar_movies":
                return tools.find_similar_movies(
                    movie_identifier=tool_input["movie_identifier"],
                    similarity_type=tool_input.get("similarity_type", "all"),
                    limit=tool_input.get("limit", 10)
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"error": f"Error executing tool {tool_name}: {str(e)}"}
        finally:
            tool_db.close()