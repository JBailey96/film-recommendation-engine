# IMDB Ratings Analyzer

A comprehensive tool to analyze your IMDB movie ratings and discover your cinematic preferences using AI-powered insights.

## 🎬 Features

- **Smart Data Collection**: Scrapes your public IMDB ratings with respectful rate limiting
- **Multi-Dimensional Analysis**: Analyzes preferences across genres, years, cast, runtime, and visual styles
- **AI-Powered Insights**: Uses Claude AI for deep personality profiling and poster style analysis
- **Interactive Dashboard**: Modern React interface with beautiful data visualizations
- **Real-time Progress**: Live updates during the scraping and analysis process

## 🏗 Architecture

### Backend (Python FastAPI)
- **Web Scraping**: Async IMDB scraping with intelligent rate limiting
- **Data Analysis**: Statistical analysis of movie preferences
- **AI Integration**: Claude API for advanced insights
- **PostgreSQL**: Robust data storage with SQLAlchemy ORM

### Frontend (React TypeScript)
- **Modern UI**: Material-UI components with dark theme
- **Data Visualization**: Interactive charts with Recharts
- **Real-time Updates**: Live progress tracking
- **Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd imdb-ratings-tool

# Copy and configure environment
cp .env.example .env
# Edit .env with your IMDB profile URL and optional Claude API key

# Start the application
docker-compose up -d

# Access at http://localhost:8000
```

### Option 2: Manual Setup

```bash
# Backend setup
pip install -r requirements.txt
createdb imdb_ratings
cd backend && python -m app.main

# Frontend setup (new terminal)
cd frontend
npm install
npm start
```

## 📊 What You'll Discover

### Genre Analysis
- Your favorite and least favorite genres
- Rating patterns across different types of films
- Genre diversity in your viewing habits

### Temporal Preferences
- Favorite decades and eras of cinema
- How your taste correlates with release years
- Trends in your rating patterns over time

### Cast & Crew Insights
- Your most-rated actors and directors
- Performance patterns of your favorites
- Hidden connections in your preferences

### Visual Style Analysis
- Poster color preferences and their correlation with ratings
- Visual style patterns (dark vs. bright, minimalist vs. complex)
- AI analysis of aesthetic preferences

### Runtime Preferences
- Optimal movie length for your enjoyment
- How runtime affects your ratings
- Patterns in your attention span preferences

### AI Personality Profile
- Deep insights into what your movie choices reveal about you
- Personality traits reflected in your cinematic taste
- Recommendations based on your unique profile

## 🔧 Configuration

### Required Setup
1. **IMDB Profile URL**: Your public ratings page (e.g., `https://www.imdb.com/user/ur12345678/ratings/`)
2. **Database**: PostgreSQL (automatically configured with Docker)

### Optional Setup
- **Claude API Key**: For advanced AI analysis and poster insights
- **Custom Rate Limiting**: Adjust scraping speed in settings

## 📈 Usage

1. **Import Data**: Enter your IMDB profile URL and start scraping
2. **Monitor Progress**: Watch real-time progress as your ratings are collected
3. **Explore Analysis**: Dive into comprehensive preference analysis
4. **Discover Insights**: Learn about your movie personality with AI insights

## 🛠 Development

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

### Database Schema
The application uses a well-structured PostgreSQL schema:
- **Movies**: Core movie information and metadata
- **UserRatings**: Your ratings and review data
- **CastMembers**: Actor and director information
- **PosterAnalysis**: AI-powered visual analysis results
- **UserPreferences**: Cached analysis results

## 🔒 Privacy & Ethics

- **Respectful Scraping**: Implements proper rate limiting and follows IMDB's robots.txt
- **Local Data**: All your data stays on your machine or chosen hosting
- **Optional AI**: Claude API integration is entirely optional
- **Public Data Only**: Only accesses your public IMDB ratings

## 📝 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints
- `POST /api/scraping/start` - Begin data collection
- `GET /api/analysis/*` - Various analysis endpoints
- `GET /api/ratings/` - Access your ratings data

## 🧪 Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- PostgreSQL (Database)
- BeautifulSoup4 (Web scraping)
- Anthropic Claude API (AI analysis)
- Scikit-learn (Data analysis)

**Frontend:**
- React 18 (UI framework)
- TypeScript (Type safety)
- Material-UI (Component library)
- Recharts (Data visualization)
- Axios (HTTP client)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (Production deployment)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- New analysis features
- UI/UX improvements
- Bug fixes
- Documentation updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal use and educational purposes. Please ensure your IMDB profile is set to public before using this tool. Always respect website terms of service and rate limits when scraping data.