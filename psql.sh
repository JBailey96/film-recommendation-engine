#!/bin/bash
# psql.sh - Connect to PostgreSQL database via CLI and run commands
# Usage: ./psql.sh [optional SQL command or file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection settings (runs inside Docker)
DB_NAME="imdb_ratings"
DB_USER="postgres"

# Function to print colored output
print_info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

print_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

# Check if Docker is running and PostgreSQL container is up
check_database() {
    print_info "Checking database connection..."
    
    if ! docker-compose ps postgres | grep -q "Up"; then
        print_error "PostgreSQL container is not running!"
        print_info "Starting Docker Compose..."
        docker-compose up -d postgres
        
        # Wait for PostgreSQL to be ready
        print_info "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; then
                print_success "PostgreSQL is ready!"
                break
            fi
            sleep 1
        done
        
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start within 30 seconds"
            exit 1
        fi
    else
        print_success "PostgreSQL container is running"
    fi
}

# Run a SQL command or file
run_sql() {
    local query="$1"
    
    if [ -f "$query" ]; then
        print_info "Executing SQL file: $query"
        cat "$query" | docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME"
    else
        print_info "Executing SQL command"
        echo "$query" | docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME"
    fi
}

# Interactive psql session
interactive_session() {
    print_info "Starting interactive PostgreSQL session inside Docker container"
    print_info "Database: $DB_NAME"
    print_warning "Type \\q to exit, \\? for help"
    echo ""
    
    docker-compose exec postgres psql -U "$DB_USER" -d "$DB_NAME"
}

# Show helpful database analysis queries
show_examples() {
    cat << 'EOF'

📊 USEFUL DATABASE ANALYSIS QUERIES:

Basic Statistics:
  SELECT COUNT(*) as total_movies FROM movies;
  SELECT COUNT(*) as total_ratings FROM user_ratings;
  SELECT AVG(rating) as avg_rating FROM user_ratings;

Top Rated Movies:
  SELECT m.title, m.year, ur.rating, m.imdb_rating 
  FROM movies m 
  JOIN user_ratings ur ON m.id = ur.movie_id 
  ORDER BY ur.rating DESC, m.imdb_rating DESC 
  LIMIT 10;

Genre Analysis:
  SELECT genre, COUNT(*) as count 
  FROM movies, unnest(genres) as genre 
  GROUP BY genre 
  ORDER BY count DESC;

Rating Distribution:
  SELECT rating, COUNT(*) as count 
  FROM user_ratings 
  GROUP BY rating 
  ORDER BY rating;

Movies by Decade:
  SELECT (year/10)*10 as decade, COUNT(*) as count 
  FROM movies 
  WHERE year IS NOT NULL 
  GROUP BY decade 
  ORDER BY decade;

Director Analysis:
  SELECT director, COUNT(*) as movie_count, AVG(ur.rating) as avg_rating 
  FROM movies m 
  JOIN user_ratings ur ON m.id = ur.movie_id 
  WHERE director IS NOT NULL 
  GROUP BY director 
  HAVING COUNT(*) >= 3 
  ORDER BY avg_rating DESC;

Chat Conversation Stats:
  SELECT COUNT(*) as total_conversations FROM chat_conversations;
  SELECT COUNT(*) as total_messages FROM chat_messages;
  SELECT role, COUNT(*) FROM chat_messages GROUP BY role;

Database Schema:
  \dt     -- List all tables
  \d movies  -- Describe movies table
  \d user_ratings  -- Describe user_ratings table

EOF
}

# Main script logic
main() {
    echo "🎬 IMDb Ratings Database CLI Tool"
    echo "================================="
    
    # Check database connection
    check_database
    
    if [ $# -eq 0 ]; then
        # No arguments - show examples and start interactive session
        show_examples
        interactive_session
    elif [ "$1" = "--examples" ] || [ "$1" = "-e" ]; then
        # Show examples only
        show_examples
    elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        # Show help
        echo "Usage:"
        echo "  ./psql.sh                    # Interactive session with examples"
        echo "  ./psql.sh \"SQL QUERY\"        # Execute single query"
        echo "  ./psql.sh query.sql          # Execute SQL file"
        echo "  ./psql.sh --examples         # Show example queries only"
        echo "  ./psql.sh --help             # Show this help"
        echo ""
        echo "Examples:"
        echo "  ./psql.sh \"SELECT COUNT(*) FROM movies;\""
        echo "  ./psql.sh analysis_queries.sql"
    else
        # Execute provided SQL command or file
        run_sql "$1"
    fi
}

# Run main function with all arguments
main "$@"