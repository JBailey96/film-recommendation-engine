from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from .database.models import Base
from .database.connection import engine
from .api import ratings, analysis, scraping

app = FastAPI(
    title="IMDB Ratings Analyzer",
    description="Analyze your IMDB ratings and discover your movie preferences",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(ratings.router, prefix="/api/ratings", tags=["ratings"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["scraping"])

# Serve static files from frontend build
frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
    app.mount("/", StaticFiles(directory=str(frontend_build_path), html=True), name="frontend")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "IMDB Ratings Analyzer API is running"}

@app.get("/")
async def root():
    return {"message": "Welcome to IMDB Ratings Analyzer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)