# Database CLI Access Guide

This guide explains how to use the `psql` scripts to connect to and analyze your IMDb ratings database.

## Prerequisites

- Docker and Docker Compose must be installed
- The IMDb ratings application must be set up (via `docker-compose up`)

## Available Scripts

### Unix/Linux/macOS: `./psql.sh`
### Windows: `psql.bat`

Both scripts provide identical functionality for accessing the PostgreSQL database.

## Usage

### 1. Interactive Session (Recommended)
Start an interactive PostgreSQL session with helpful examples:

```bash
# Unix/Linux/macOS
./psql.sh

# Windows
psql.bat
```

This will:
- Check if PostgreSQL is running (starts it if needed)
- Display useful analysis queries
- Open an interactive psql session

### 2. Execute Single Query
Run a single SQL command:

```bash
# Unix/Linux/macOS
./psql.sh "SELECT COUNT(*) FROM movies;"

# Windows  
psql.bat "SELECT COUNT(*) FROM movies;"
```

### 3. Execute SQL File
Run queries from a SQL file:

```bash
# Unix/Linux/macOS
./psql.sh my_queries.sql

# Windows
psql.bat my_queries.sql
```

### 4. Show Examples Only
Display helpful queries without opening interactive session:

```bash
# Unix/Linux/macOS
./psql.sh --examples

# Windows
psql.bat --examples
```

### 5. Show Help
Display usage information:

```bash
# Unix/Linux/macOS
./psql.sh --help

# Windows
psql.bat --help
```

## Useful Database Analysis Queries

### Basic Statistics
```sql
-- Total number of movies in your collection
SELECT COUNT(*) as total_movies FROM movies;

-- Total number of ratings you've given
SELECT COUNT(*) as total_ratings FROM user_ratings;

-- Your average rating
SELECT AVG(rating) as avg_rating FROM user_ratings;

-- Rating distribution
SELECT rating, COUNT(*) as count 
FROM user_ratings 
GROUP BY rating 
ORDER BY rating;
```

### Movie Analysis
```sql
-- Your top 10 rated movies
SELECT m.title, m.year, ur.rating, m.imdb_rating 
FROM movies m 
JOIN user_ratings ur ON m.id = ur.movie_id 
ORDER BY ur.rating DESC, m.imdb_rating DESC 
LIMIT 10;

-- Movies by decade
SELECT (year/10)*10 as decade, COUNT(*) as count 
FROM movies 
WHERE year IS NOT NULL 
GROUP BY decade 
ORDER BY decade;

-- Most watched genres
SELECT genre, COUNT(*) as count 
FROM movies, unnest(genres) as genre 
GROUP BY genre 
ORDER BY count DESC;
```

### Director Analysis
```sql
-- Directors with multiple movies and their average rating from you
SELECT director, COUNT(*) as movie_count, AVG(ur.rating) as avg_rating 
FROM movies m 
JOIN user_ratings ur ON m.id = ur.movie_id 
WHERE director IS NOT NULL 
GROUP BY director 
HAVING COUNT(*) >= 3 
ORDER BY avg_rating DESC;
```

### Runtime Analysis
```sql
-- Average runtime of movies you've rated highly (8+)
SELECT AVG(runtime_minutes) as avg_runtime
FROM movies m 
JOIN user_ratings ur ON m.id = ur.movie_id 
WHERE ur.rating >= 8;

-- Runtime distribution
SELECT 
  CASE 
    WHEN runtime_minutes < 90 THEN 'Short (<90m)'
    WHEN runtime_minutes < 120 THEN 'Medium (90-120m)'
    WHEN runtime_minutes < 150 THEN 'Long (120-150m)'
    ELSE 'Very Long (150m+)'
  END as length_category,
  COUNT(*) as count,
  AVG(ur.rating) as avg_rating
FROM movies m 
JOIN user_ratings ur ON m.id = ur.movie_id 
WHERE runtime_minutes IS NOT NULL
GROUP BY length_category
ORDER BY avg_rating DESC;
```

### Chat Analysis
```sql
-- Chat conversation statistics
SELECT COUNT(*) as total_conversations FROM chat_conversations;
SELECT COUNT(*) as total_messages FROM chat_messages;
SELECT role, COUNT(*) FROM chat_messages GROUP BY role;

-- Recent chat activity
SELECT 
  cc.title,
  COUNT(cm.id) as message_count,
  MAX(cm.timestamp) as last_message
FROM chat_conversations cc
LEFT JOIN chat_messages cm ON cc.conversation_id = cm.conversation_id
WHERE cc.is_saved = true
GROUP BY cc.id, cc.title
ORDER BY last_message DESC;
```

## Database Schema

Use these commands in the interactive session to explore the database structure:

```sql
-- List all tables
\dt

-- Describe specific tables
\d movies
\d user_ratings  
\d chat_conversations
\d chat_messages
\d cast_members

-- View table sizes
SELECT 
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public';
```

## Tips

1. **Use LIMIT**: Always use `LIMIT` when exploring large datasets to avoid overwhelming output
2. **Save Queries**: Create `.sql` files for complex queries you use frequently
3. **Export Results**: Use `\copy` command to export query results to CSV files
4. **Performance**: Use `EXPLAIN ANALYZE` to understand query performance

## Troubleshooting

### Database Not Running
If you get connection errors:
```bash
docker-compose up -d postgres
```

### Permission Errors (Unix/Linux/macOS)
Make the script executable:
```bash
chmod +x psql.sh
```

### Docker Issues
Ensure Docker is running and you have the necessary permissions:
```bash
docker ps
docker-compose ps
```

## Advanced Usage

### Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres imdb_ratings > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres imdb_ratings
```

### Monitor Database Activity
```bash
# Show current connections
./psql.sh "SELECT * FROM pg_stat_activity;"

# Show table sizes  
./psql.sh "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(tablename)) FROM pg_tables WHERE schemaname='public';"
```