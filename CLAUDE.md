# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive IMDB ratings analysis tool that scrapes user ratings from IMDB, analyzes preferences across multiple dimensions, and provides detailed insights using AI. The application consists of a Python FastAPI backend with PostgreSQL database and a React TypeScript frontend.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- (Optional) Claude API key for advanced analysis

### Quick Start with Docker
```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Access the application at http://localhost:8000
```

### Manual Development Setup
```bash
# Activate virtual environment (if exists)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Backend setup
pip install -r requirements.txt
createdb imdb_ratings
cd backend && python -m app.main

# Frontend setup (in another terminal)
cd frontend
npm install
npm start
```

### Virtual Environment
This project uses a Python virtual environment located in the `venv/` directory. Always activate it before running Python commands:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

## Common Commands

### Development
- `npm run dev` - Start both backend and frontend in development mode
- `npm run backend` - Start only the FastAPI backend server
- `npm run frontend` - Start only the React development server
- `npm run install-all` - Install all dependencies (Python + Node.js)

### Database
- `npm run setup-db` - Run database migrations
- `docker-compose exec postgres psql -U postgres -d imdb_ratings` - Access database

### Data Processing
- `npm run scrape` - Start IMDB scraping process
- Access scraping controls via the web interface at `/import-data`

### Docker Operations
- `docker-compose up -d` - Start all services
- `docker-compose down` - Stop all services
- `docker-compose logs app` - View application logs

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/                 # API route handlers
│   │   ├── database/            # Database models and connection
│   │   ├── scraper/             # IMDB scraping functionality
│   │   ├── analysis/            # Data analysis and ML modules
│   │   └── schemas/             # Pydantic schemas for API
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # Main application pages
│   │   ├── components/          # Reusable React components
│   │   ├── services/            # API communication
│   │   └── types/               # TypeScript type definitions
│   └── package.json
├── scripts/                     # Deployment and utility scripts
└── docker-compose.yml          # Complete application stack
```

## Architecture Notes

### Backend Architecture
- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: Database ORM with PostgreSQL backend
- **Async Processing**: Non-blocking web scraping with rate limiting
- **Modular Analysis**: Separate modules for different analysis types (genres, cast, posters, etc.)

### Data Processing Pipeline
1. **Scraping**: Respectful IMDB scraping with rate limiting and error handling
2. **Data Enrichment**: Fetches detailed movie information for each rating
3. **Analysis**: Multiple analysis modules for different preference dimensions
4. **AI Integration**: Claude API integration for deep insights and poster analysis

### Frontend Architecture
- **React 18**: Modern React with hooks and functional components
- **Material-UI**: Professional UI component library with dark theme
- **TypeScript**: Type-safe development
- **Recharts**: Data visualization for analysis results

### Key Features
- **Genre Analysis**: Preference patterns across movie genres
- **Temporal Analysis**: Decade and year preference trends
- **Cast Analysis**: Favorite actors and directors identification
- **Runtime Preferences**: Movie length preference analysis
- **Visual Style Analysis**: Poster color and style preference analysis using AI
- **Overall Insights**: Comprehensive personality profiling using Claude AI

## API Endpoints

### Ratings
- `GET /api/ratings/` - Get all user ratings with filtering and pagination
- `GET /api/ratings/stats` - Get overall rating statistics
- `GET /api/ratings/{imdb_id}` - Get specific movie rating

### Scraping
- `POST /api/scraping/start` - Start IMDB scraping process
- `GET /api/scraping/status` - Get current scraping status and progress
- `POST /api/scraping/stop` - Stop active scraping
- `DELETE /api/scraping/reset` - Reset all data

### Analysis
- `GET /api/analysis/genres` - Genre preference analysis
- `GET /api/analysis/years` - Year/decade preference analysis
- `GET /api/analysis/runtime` - Runtime preference analysis
- `GET /api/analysis/cast` - Cast and crew preference analysis
- `GET /api/analysis/poster-style` - Visual style preference analysis
- `GET /api/analysis/insights` - Overall AI-generated insights

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `CLAUDE_API_KEY` - Optional Claude API key for advanced analysis
- `API_HOST` and `API_PORT` - Backend server configuration
- `REACT_APP_API_URL` - Frontend API endpoint configuration

### Key Files
- `.env` - Environment configuration (copy from `.env.example`)
- `backend/app/database/connection.py` - Database configuration
- `frontend/src/services/api.ts` - Frontend API client
- `docker-compose.yml` - Complete application stack definition

## Development Notes

### Adding New Analysis Types
1. Create analysis function in `backend/app/analysis/`
2. Add corresponding API endpoint in `backend/app/api/analysis.py`
3. Create TypeScript types in `frontend/src/services/api.ts`
4. Add UI components in `frontend/src/pages/AnalysisPage.tsx`

### Database Schema
- All tables are defined in `backend/app/database/models.py`
- Database migrations are handled automatically on startup
- Poster analysis data is stored as JSON for flexibility

### Rate Limiting
- Configurable delays between IMDB requests (default: 2 seconds)
- Automatic retry logic for rate limit responses
- Graceful error handling for failed requests

### AI Integration
- Claude API used for poster style analysis and overall insights
- Fallback behavior when API key not provided
- Structured prompts for consistent analysis quality