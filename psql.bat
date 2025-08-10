@echo off
:: psql.bat - Connect to PostgreSQL database via CLI and run commands (Windows)
:: Usage: psql.bat [optional SQL command or file]

setlocal enabledelayedexpansion

:: Database connection settings
set DB_HOST=localhost
set DB_PORT=5433
set DB_NAME=imdb_ratings
set DB_USER=imdb_app
set DB_PASSWORD=""

echo 🎬 IMDb Ratings Database CLI Tool
echo =================================

:: Check if Docker is running and PostgreSQL container is up
echo INFO: Checking database connection...

docker-compose ps postgres | findstr "Up" >nul
if errorlevel 1 (
    echo ERROR: PostgreSQL container is not running!
    echo INFO: Starting Docker Compose...
    docker-compose up -d postgres
    
    echo INFO: Waiting for PostgreSQL to be ready...
    timeout /t 10 /nobreak >nul
    
    :: Check if PostgreSQL is ready
    docker-compose exec postgres pg_isready -U postgres >nul 2>&1
    if errorlevel 1 (
        echo ERROR: PostgreSQL failed to start
        exit /b 1
    )
    echo SUCCESS: PostgreSQL is ready!
) else (
    echo SUCCESS: PostgreSQL container is running
)

:: Handle command line arguments
if "%~1"=="" goto interactive
if "%~1"=="--examples" goto examples
if "%~1"=="-e" goto examples
if "%~1"=="--help" goto help
if "%~1"=="-h" goto help

:: Execute SQL command or file
if exist "%~1" (
    echo INFO: Executing SQL file: %~1
    type "%~1" | docker-compose exec -T postgres psql -U %DB_USER% -d %DB_NAME%
) else (
    echo INFO: Executing SQL command
    echo %~1 | docker-compose exec -T postgres psql -U %DB_USER% -d %DB_NAME%
)
goto end

:interactive
call :show_examples
echo INFO: Starting interactive PostgreSQL session
echo INFO: Database: %DB_NAME%
echo WARNING: Type \q to exit, \? for help
echo.
docker-compose exec postgres psql -U %DB_USER% -d %DB_NAME%
goto end

:examples
call :show_examples
goto end

:help
echo Usage:
echo   psql.bat                     # Interactive session with examples
echo   psql.bat "SQL QUERY"         # Execute single query
echo   psql.bat query.sql           # Execute SQL file
echo   psql.bat --examples          # Show example queries only
echo   psql.bat --help              # Show this help
echo.
echo Examples:
echo   psql.bat "SELECT COUNT(*) FROM movies;"
echo   psql.bat analysis_queries.sql
goto end

:show_examples
echo.
echo 📊 USEFUL DATABASE ANALYSIS QUERIES:
echo.
echo Basic Statistics:
echo   SELECT COUNT(*) as total_movies FROM movies;
echo   SELECT COUNT(*) as total_ratings FROM user_ratings;
echo   SELECT AVG(rating) as avg_rating FROM user_ratings;
echo.
echo Top Rated Movies:
echo   SELECT m.title, m.year, ur.rating, m.imdb_rating 
echo   FROM movies m 
echo   JOIN user_ratings ur ON m.id = ur.movie_id 
echo   ORDER BY ur.rating DESC, m.imdb_rating DESC 
echo   LIMIT 10;
echo.
echo Genre Analysis:
echo   SELECT genre, COUNT(*) as count 
echo   FROM movies, unnest(genres) as genre 
echo   GROUP BY genre 
echo   ORDER BY count DESC;
echo.
echo Rating Distribution:
echo   SELECT rating, COUNT(*) as count 
echo   FROM user_ratings 
echo   GROUP BY rating 
echo   ORDER BY rating;
echo.
echo Movies by Decade:
echo   SELECT (year/10)*10 as decade, COUNT(*) as count 
echo   FROM movies 
echo   WHERE year IS NOT NULL 
echo   GROUP BY decade 
echo   ORDER BY decade;
echo.
echo Director Analysis:
echo   SELECT director, COUNT(*) as movie_count, AVG(ur.rating) as avg_rating 
echo   FROM movies m 
echo   JOIN user_ratings ur ON m.id = ur.movie_id 
echo   WHERE director IS NOT NULL 
echo   GROUP BY director 
echo   HAVING COUNT(*) ^>= 3 
echo   ORDER BY avg_rating DESC;
echo.
echo Chat Conversation Stats:
echo   SELECT COUNT(*) as total_conversations FROM chat_conversations;
echo   SELECT COUNT(*) as total_messages FROM chat_messages;
echo   SELECT role, COUNT(*) FROM chat_messages GROUP BY role;
echo.
echo Database Schema:
echo   \dt     -- List all tables
echo   \d movies  -- Describe movies table
echo   \d user_ratings  -- Describe user_ratings table
echo.
exit /b 0

:end
endlocal