# IMDb Ratings Analysis Tool

A comprehensive IMDb movie ratings analysis platform that transforms your rating history into deep insights about your cinematic preferences. Features AI-powered analysis, interactive chat, visual poster integration, and intelligent recommendation capabilities.

## 🎬 Features

### Core Analysis
- **Multi-Dimensional Analysis**: Deep analysis across genres, decades, cast, runtime, and visual styles
- **AI-Powered Insights**: Claude AI integration for personality profiling and comprehensive preference analysis
- **Visual Movie Browser**: High-quality movie posters from The Movie Database (TMDb)
- **Interactive Dashboard**: Modern React interface with beautiful data visualizations

### Advanced Functionality
- **Conversational AI Chat**: Discuss your movie preferences with Claude AI and save important conversations
- **Flexible Data Import**: Simple CSV upload system with incremental data processing
- **Database CLI Tools**: Direct database access with comprehensive analysis queries
- **Model Context Protocol**: MCP server integration for seamless Claude Code interaction

## 🏗 Architecture

### Backend (Python FastAPI)
- **CSV Data Processing**: Incremental import system for IMDb ratings data
- **Multi-Modal Analysis**: Statistical analysis across multiple preference dimensions
- **AI Integration**: Claude API for conversational chat and advanced insights
- **PostgreSQL with Socket Communication**: Secure database storage with Unix socket connections
- **TMDb API Integration**: High-quality movie poster and metadata enrichment

### Frontend (React TypeScript)
- **Modern Material-UI Interface**: Professional dark theme with responsive design
- **Interactive Data Visualization**: Dynamic charts and analysis displays
- **Conversational Chat System**: Save/load conversations with AI analysis
- **Movie Grid with Posters**: Visual movie browser with TMDb poster integration
- **Real-time Progress Tracking**: Live updates during data processing

### Infrastructure & Integration
- **Docker Compose Stack**: Complete containerized application with health checks
- **MCP Server**: Model Context Protocol server for Claude Code integration
- **Cross-platform CLI Tools**: Database access scripts for Windows and Unix systems
- **Secure Configuration**: Environment-based secrets management

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd imdb-ratings-tool

# Copy and configure environment
cp .env.example .env
# Edit .env with optional TMDb API key and Claude API key

# Start all services (web app + database + MCP server)
docker-compose up -d

# Access the application at http://localhost:8000
# - Dashboard: Main analytics and poster enrichment
# - Chat: AI-powered conversation about your movie preferences  
# - All Ratings: Visual movie browser with posters
# - Analysis: Deep preference insights across multiple dimensions
# - Import Data: CSV file upload for your IMDb ratings
```

### Option 2: Manual Development Setup

```bash
# Activate virtual environment (if exists)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Backend setup
pip install -r requirements.txt
createdb imdb_ratings
cd backend && python -m app.main

# Frontend setup (new terminal)
cd frontend
npm install
npm start

# Access at http://localhost:3000 (development) or http://localhost:8000 (production)
```

### MCP Server Integration (Claude Code)

The application includes a Model Context Protocol server for seamless integration with Claude Code:

```bash
# MCP server runs automatically with Docker Compose
# Provides these tools to Claude Code:
# - search_movies: Find movies by title, director, or cast
# - get_movie_details: Get detailed movie information
# - filter_movies: Filter movies by criteria (genre, year, rating)
# - get_movie_stats: Get collection statistics
# - find_similar_movies: Find movies similar to a given movie
# - get_cast_member_movies: Get all movies for a cast member
```

## 📊 What You'll Discover

### Comprehensive Analysis Dashboard
- **Movie Collection Overview**: Visual statistics with high-quality poster displays
- **Rating Distribution**: Interactive charts showing your rating patterns
- **Poster Enrichment**: One-click enhancement using The Movie Database API

### Multi-Dimensional Preference Analysis
- **Genre Analysis**: Favorite and least favorite genres with rating correlations
- **Temporal Preferences**: Decade preferences and cinematic era insights
- **Cast & Crew Insights**: Most-rated actors, directors, and collaboration patterns
- **Runtime Preferences**: Optimal movie length analysis and attention patterns
- **Visual Style Analysis**: AI-powered poster aesthetics and color preference analysis

### Interactive AI Chat System
- **Conversational Analysis**: Discuss your preferences with Claude AI in natural language
- **Conversation Management**: Save and load up to 10 important conversation threads
- **Deep Insights**: Get personalized explanations about your cinematic personality
- **Dynamic Questioning**: AI asks follow-up questions to understand your tastes better

### Visual Movie Experience
- **Poster Integration**: High-resolution movie posters for visual movie identification
- **Grid Layout**: Browse your entire collection visually with ratings overlay
- **Search and Filter**: Find movies by title, year, rating, or visual browsing

## 🔧 Configuration

### Environment Setup
Create a `.env` file from `.env.example` and configure:

```bash
# Database (automatically configured with Docker)
DATABASE_URL=postgresql://imdb_app@localhost/imdb_ratings

# Optional API Keys
CLAUDE_API_KEY=your_claude_api_key_here  # For AI chat and insights
TMDB_API_KEY=your_tmdb_api_key_here      # For movie posters (recommended)

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### Required Setup
1. **Database**: PostgreSQL (automatically configured with Docker using secure Unix sockets)
2. **IMDb CSV Export**: Export your ratings from IMDb as CSV file

### Optional Setup
- **Claude API Key**: Enables AI-powered chat functionality and deep personality insights
- **TMDb API Key**: Enables high-quality movie poster integration (free tier available)

## 📈 Usage Guide

### Getting Started
1. **Start Services**: Run `docker-compose up -d` to start all services
2. **Import Data**: Use the "Import Data" tab to upload your IMDb ratings CSV file
3. **Enrich Posters**: Click "Enrich Posters" on the Dashboard to add movie images
4. **Explore Analysis**: Navigate through different analysis tabs
5. **Chat with AI**: Use the Chat tab to discuss your preferences (requires Claude API key)

### Data Import Process
- **CSV Upload**: Drag and drop your IMDb ratings CSV file
- **Incremental Processing**: New imports only add missing movies, no duplicates
- **Progress Tracking**: Real-time progress updates during processing
- **Error Handling**: Graceful handling of malformed data with detailed feedback

### Database Access
Use the provided CLI tools for direct database access:

```bash
# Linux/Mac
./psql.sh                    # Interactive session with example queries
./psql.sh "SELECT COUNT(*) FROM movies;"  # Execute single query

# Windows  
psql.bat                     # Interactive session with example queries
psql.bat "SELECT COUNT(*) FROM movies;"   # Execute single query
```

## 🛠 Development

### Development Commands
```bash
# All-in-one development setup
npm run install-all     # Install both Python and Node.js dependencies
npm run dev            # Start both backend and frontend in development mode
npm run backend        # Start only FastAPI backend server
npm run frontend       # Start only React development server
npm run setup-db       # Run database migrations
```

### Adding New Analysis Features

```python
# 1. Create analysis function in backend/app/analysis/
async def analyze_new_feature(self):
    # Your analysis logic here
    return analysis_result

# 2. Add API endpoint in backend/app/api/analysis.py
@router.get("/new-feature")
async def get_new_analysis():
    return await analyzer.analyze_new_feature()

# 3. Add frontend integration in frontend/src/services/api.ts
static async getNewAnalysis(): Promise<NewAnalysisType> {
    const response = await api.get('/api/analysis/new-feature');
    return response.data;
}
```

### Docker Development
```bash
# View logs for specific services
docker-compose logs app          # Web application logs
docker-compose logs postgres     # Database logs  
docker-compose logs mcp-server   # MCP server logs

# Access running containers
docker-compose exec app bash     # Access web app container
docker-compose exec postgres psql -U imdb_app -d imdb_ratings  # Database access
```

### Database Schema
The application uses a comprehensive PostgreSQL schema with secure socket communication:
- **Movies**: Core movie information, genres, cast, and TMDb poster URLs
- **UserRatings**: Your ratings and review data with timestamps
- **ChatConversations**: Saved AI conversation threads with titles
- **ChatMessages**: Individual messages in conversations with role tracking
- **CastMembers**: Actor and director information with movie relationships
- **PosterAnalysis**: AI-powered visual analysis results (when Claude API available)

## 🔒 Privacy & Security

- **Local Data Control**: All your data stays on your machine or chosen hosting environment
- **Secure Database Communication**: Unix socket-based PostgreSQL connections within Docker
- **Environment-Based Secrets**: API keys stored in environment variables, never in code
- **Optional AI Integration**: Claude API and TMDb API usage is entirely optional
- **CSV-Based Import**: No web scraping required, you control your data import process

## 📝 API Documentation

Once running, visit `http://localhost:8000/docs` for comprehensive interactive API documentation.

### Key API Endpoints

#### Data Management
- `POST /api/scraping/upload-csv` - Upload IMDb ratings CSV file
- `GET /api/scraping/status` - Get import progress and status
- `POST /api/ratings/enrich-posters` - Enrich movies with TMDb poster data

#### Analysis & Insights  
- `GET /api/analysis/genres` - Genre preference analysis
- `GET /api/analysis/years` - Temporal preference analysis
- `GET /api/analysis/cast` - Cast and crew preference analysis
- `GET /api/analysis/runtime` - Runtime preference analysis
- `GET /api/analysis/poster-style` - Visual style preference analysis
- `GET /api/analysis/insights` - AI-powered overall insights

#### Chat & Conversations
- `POST /api/chat/conversations` - Start new AI conversation
- `GET /api/chat/conversations` - List saved conversations
- `POST /api/chat/conversations/save` - Save conversation with custom title
- `DELETE /api/chat/conversations/{id}` - Delete saved conversation

#### Movie Data Access
- `GET /api/ratings/` - Get ratings with filtering and pagination
- `GET /api/ratings/stats` - Get collection statistics
- `GET /api/ratings/{imdb_id}` - Get specific movie details

## 🧪 Technology Stack

**Backend:**
- **FastAPI** - Modern Python web framework with automatic OpenAPI documentation
- **SQLAlchemy** - Database ORM with async support
- **PostgreSQL 15** - Robust database with secure Unix socket communication
- **Anthropic Claude API** - AI-powered conversational analysis and insights
- **The Movie Database (TMDb) API** - High-quality movie posters and metadata
- **Pandas** - Data analysis and CSV processing

**Frontend:**
- **React 18** - Modern UI framework with hooks and concurrent features
- **TypeScript** - Type-safe development with excellent IDE support
- **Material-UI (MUI)** - Professional component library with dark theme
- **Recharts** - Interactive data visualization components
- **Axios** - HTTP client with request/response interceptors

**Infrastructure & Integration:**
- **Docker & Docker Compose** - Complete containerized application stack
- **Model Context Protocol (MCP)** - Integration with Claude Code for data analysis
- **Unix Socket Communication** - Secure database connections within containers
- **Cross-platform CLI Tools** - Direct database access on Windows and Unix systems

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

**Feature Enhancements:**
- New analysis algorithms and preference insights
- Additional API integrations (streaming services, review aggregators)
- Enhanced conversation AI capabilities
- Advanced recommendation system features

**Technical Improvements:**
- Performance optimizations and caching strategies  
- Enhanced security and authentication features
- Mobile responsiveness improvements
- Database query optimization

**User Experience:**
- UI/UX design improvements
- Accessibility enhancements
- Internationalization and localization
- Error handling and user feedback improvements

### Development Setup
1. Fork the repository and clone your fork
2. Follow the "Manual Development Setup" instructions above
3. Create a feature branch for your changes
4. Submit a pull request with a clear description of your improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- **[Claude Code Documentation](https://docs.anthropic.com/claude-code)** - For MCP server integration
- **[The Movie Database API](https://developers.themoviedb.org/3)** - For poster and metadata integration  
- **[IMDb CSV Export Guide](https://help.imdb.com/article/imdb/discover-watch/ratings/G56VBEQMZBRZXKQM)** - How to export your IMDb ratings
- **[APPLICATION-IMPROVEMENTS.md](APPLICATION-IMPROVEMENTS.md)** - Detailed documentation of completed improvements and future recommendation system plans

## ⚠️ Disclaimer

This tool is for personal analysis of your own IMDb rating data. The application respects data privacy by:
- Processing only your exported CSV data (no web scraping required)
- Storing all data locally or in your chosen hosting environment  
- Making API calls only with your explicit API keys
- Never sharing your data with external services beyond the APIs you configure

Always review privacy policies for any APIs you choose to integrate (Claude AI, TMDb).