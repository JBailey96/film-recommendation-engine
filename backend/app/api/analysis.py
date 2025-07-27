from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database.connection import get_db
from ..database.models import Movie, UserRating, CastMember, PosterAnalysis, UserPreferences
from ..analysis.preferences import PreferenceAnalyzer
from ..analysis.poster_analyzer import PosterAnalyzer
from ..schemas.analysis import (
    GenreAnalysis, YearAnalysis, RuntimeAnalysis, 
    CastAnalysis, PosterStyleAnalysis, OverallInsights
)

router = APIRouter()

@router.get("/genres", response_model=GenreAnalysis)
async def analyze_genre_preferences(db: Session = Depends(get_db)):
    """Analyze user's genre preferences"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.analyze_genres()

@router.get("/years", response_model=YearAnalysis) 
async def analyze_year_preferences(db: Session = Depends(get_db)):
    """Analyze user's preferences by movie year/decade"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.analyze_years()

@router.get("/runtime", response_model=RuntimeAnalysis)
async def analyze_runtime_preferences(db: Session = Depends(get_db)):
    """Analyze user's preferences by movie runtime"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.analyze_runtime()

@router.get("/cast", response_model=CastAnalysis)
async def analyze_cast_preferences(db: Session = Depends(get_db)):
    """Analyze user's favorite actors and directors"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.analyze_cast()

@router.get("/poster-style", response_model=PosterStyleAnalysis)
async def analyze_poster_preferences(db: Session = Depends(get_db)):
    """Analyze user's poster style preferences"""
    analyzer = PosterAnalyzer(db)
    return await analyzer.analyze_poster_styles()

@router.get("/insights", response_model=OverallInsights)
async def get_overall_insights(db: Session = Depends(get_db)):
    """Get comprehensive insights about user preferences using LLM analysis"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.generate_overall_insights()

@router.post("/regenerate/{analysis_type}")
async def regenerate_analysis(analysis_type: str, db: Session = Depends(get_db)):
    """Regenerate a specific type of analysis"""
    valid_types = ["genres", "years", "runtime", "cast", "poster-style", "insights"]
    
    if analysis_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid analysis type. Must be one of: {valid_types}")
    
    analyzer = PreferenceAnalyzer(db)
    
    if analysis_type == "genres":
        result = await analyzer.analyze_genres(force_regenerate=True)
    elif analysis_type == "years":
        result = await analyzer.analyze_years(force_regenerate=True)
    elif analysis_type == "runtime":
        result = await analyzer.analyze_runtime(force_regenerate=True)
    elif analysis_type == "cast":
        result = await analyzer.analyze_cast(force_regenerate=True)
    elif analysis_type == "poster-style":
        poster_analyzer = PosterAnalyzer(db)
        result = await poster_analyzer.analyze_poster_styles(force_regenerate=True)
    elif analysis_type == "insights":
        result = await analyzer.generate_overall_insights(force_regenerate=True)
    
    return {"status": "completed", "analysis_type": analysis_type, "result": result}

@router.get("/recommendations")
async def get_recommendations(limit: int = 10, db: Session = Depends(get_db)):
    """Get movie recommendations based on user preferences"""
    analyzer = PreferenceAnalyzer(db)
    return await analyzer.generate_recommendations(limit=limit)