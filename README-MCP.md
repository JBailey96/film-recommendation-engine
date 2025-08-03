# IMDb Ratings MCP Server

An MCP (Model Context Protocol) server that provides comprehensive access to your IMDb ratings database for AI assistants.

## Features

The MCP server provides versatile movie data access through these tools:

- **search_movies**: Search by title, director, or cast member name
- **get_movie_details**: Get detailed movie information including cast and poster analysis
- **get_cast_member_movies**: Find all movies by a specific actor/director/writer
- **filter_movies**: Filter by genre, year, rating, runtime with sorting options
- **get_movie_stats**: Overall collection statistics
- **find_similar_movies**: Find movies similar by genre, director, or cast

## Setup

### Option 1: Docker (Recommended)

1. Start the full application stack:
```bash
docker-compose up -d
```

2. Use the Docker configuration in your MCP client:
```json
{
  "mcpServers": {
    "imdb-ratings-tool": {
      "command": "docker",
      "args": ["exec", "-i", "imdb-ratings-tool-mcp-server-1", "python", "mcp_server.py"],
      "env": {}
    }
  }
}
```

### Option 2: Local Development

1. Install MCP requirements:
```bash
pip install -r requirements-mcp.txt
```

2. Ensure your database is running (locally or via Docker):
```bash
# If using Docker for database only:
docker-compose up postgres -d
```

3. Use the local configuration:
```json
{
  "mcpServers": {
    "imdb-ratings-tool": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5433/imdb_ratings"
      }
    }
  }
}
```

## Usage Examples

Once configured with your MCP client (like Claude Desktop), you can ask natural language questions:

### Movie Queries
- "What movies has Tom Hanks been in?"
- "Show me details about The Shawshank Redemption"
- "Find action movies from the 1990s that I rated 9 or 10"
- "What are my highest rated movies?"

### Cast Queries
- "What other movies did Christopher Nolan direct?"
- "Find movies with both Leonardo DiCaprio and Marion Cotillard"
- "Show me all the actors in Inception"

### Analysis Queries
- "What are my movie collection statistics?"
- "Find movies similar to Blade Runner"
- "Show me comedy movies under 2 hours that I haven't rated yet"

### Complex Queries
- "Find sci-fi movies from 2010-2020 with IMDb ratings above 8.0"
- "What movies did I rate 10/10 and what genres are they?"
- "Show me movies by directors I seem to like (high average ratings)"

## Available Tools

### search_movies
Search for movies by title, director, or cast member name.
```
Parameters: query (string), limit (integer, default: 10)
```

### get_movie_details  
Get comprehensive movie information including cast and poster analysis.
```
Parameters: identifier (string - title or IMDb ID)
```

### get_cast_member_movies
Find all movies featuring a specific person.
```
Parameters: name (string), role_filter (optional: "actor", "director", "writer")
```

### filter_movies
Advanced filtering with multiple criteria.
```
Parameters: genres, year_min/max, user_rating_min/max, imdb_rating_min, 
           runtime_min/max, sort_by, order, limit
```

### get_movie_stats
Get overall statistics about your movie collection.
```
Parameters: none
```

### find_similar_movies
Find movies similar to a reference movie.
```
Parameters: movie_identifier, similarity_type ("genre", "director", "cast", "all"), limit
```

## Data Structure

The server provides rich movie data including:
- Basic info: title, year, director, genres, runtime, ratings
- Cast details: actors with characters, directors, writers
- Advanced data: poster analysis, color palettes, style tags
- User data: personal ratings, reviews, rating dates

## Troubleshooting

1. **Database Connection Issues**: Ensure PostgreSQL is running and accessible
2. **Docker Issues**: Check that containers are running with `docker-compose ps`
3. **MCP Client Issues**: Verify the MCP configuration matches your setup (Docker vs local)
4. **Permission Issues**: Ensure the MCP server has access to the database

## Development

The MCP server code is in `mcp_server.py` and uses the same database models as the main application. It's designed to be stateless and efficient for AI assistant interactions.