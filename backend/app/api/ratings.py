from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from ..database.connection import get_db
from ..database.models import Movie, UserRating, CastMember
from ..schemas.ratings import MovieResponse, RatingResponse, MovieStats, PaginatedRatingsResponse

router = APIRouter()

@router.get("/", response_model=PaginatedRatingsResponse)
async def get_all_ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("rated_at", regex="^(rating|rated_at|title|year|imdb_rating|runtime_minutes)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    genre_filter: Optional[str] = None,
    genres: Optional[List[str]] = Query(None),
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    rating_min: Optional[int] = Query(None, ge=1, le=10),
    rating_max: Optional[int] = Query(None, ge=1, le=10),
    imdb_rating_min: Optional[float] = Query(None, ge=0, le=10),
    imdb_rating_max: Optional[float] = Query(None, ge=0, le=10),
    runtime_min: Optional[int] = Query(None, ge=0),
    runtime_max: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    """Get all user ratings with comprehensive filtering, searching, and sorting"""
    # Base query with joins
    query = db.query(Movie, UserRating).join(UserRating)
    count_query = db.query(func.count(Movie.id)).join(UserRating)
    
    # Apply search filter
    if search:
        search_filter = or_(
            Movie.title.ilike(f"%{search}%"),
            Movie.director.ilike(f"%{search}%"),
            Movie.imdb_id.in_(
                db.query(Movie.imdb_id)
                .join(CastMember)
                .filter(CastMember.name.ilike(f"%{search}%"))
            )
        )
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)
    
    # Apply genre filters
    if genre_filter:
        genre_condition = Movie.genres.contains([genre_filter])
        query = query.filter(genre_condition)
        count_query = count_query.filter(genre_condition)
    
    if genres:
        # Filter movies that contain ANY of the specified genres
        genre_conditions = [Movie.genres.contains([genre]) for genre in genres]
        genre_filter_condition = or_(*genre_conditions)
        query = query.filter(genre_filter_condition)
        count_query = count_query.filter(genre_filter_condition)
    
    # Apply year filters
    if year_min:
        year_condition = Movie.year >= year_min
        query = query.filter(year_condition)
        count_query = count_query.filter(year_condition)
    if year_max:
        year_condition = Movie.year <= year_max
        query = query.filter(year_condition)
        count_query = count_query.filter(year_condition)
    
    # Apply user rating filters
    if rating_min:
        rating_condition = UserRating.rating >= rating_min
        query = query.filter(rating_condition)
        count_query = count_query.filter(rating_condition)
    if rating_max:
        rating_condition = UserRating.rating <= rating_max
        query = query.filter(rating_condition)
        count_query = count_query.filter(rating_condition)
    
    # Apply IMDB rating filters
    if imdb_rating_min:
        imdb_condition = Movie.imdb_rating >= imdb_rating_min
        query = query.filter(imdb_condition)
        count_query = count_query.filter(imdb_condition)
    if imdb_rating_max:
        imdb_condition = Movie.imdb_rating <= imdb_rating_max
        query = query.filter(imdb_condition)
        count_query = count_query.filter(imdb_condition)
    
    # Apply runtime filters
    if runtime_min:
        runtime_condition = Movie.runtime_minutes >= runtime_min
        query = query.filter(runtime_condition)
        count_query = count_query.filter(runtime_condition)
    if runtime_max:
        runtime_condition = Movie.runtime_minutes <= runtime_max
        query = query.filter(runtime_condition)
        count_query = count_query.filter(runtime_condition)
    
    # Apply sorting
    if sort_by == "rating":
        order_column = UserRating.rating
    elif sort_by == "rated_at":
        order_column = UserRating.rated_at
    elif sort_by == "title":
        order_column = Movie.title
    elif sort_by == "year":
        order_column = Movie.year
    elif sort_by == "imdb_rating":
        order_column = Movie.imdb_rating
    elif sort_by == "runtime_minutes":
        order_column = Movie.runtime_minutes
    
    if order == "desc":
        order_column = order_column.desc()
    
    query = query.order_by(order_column)
    
    # Get total count
    total_count = count_query.scalar()
    
    # Apply pagination
    results = query.offset(skip).limit(limit).all()
    
    ratings = [
        RatingResponse(
            movie=MovieResponse.from_orm(movie),
            rating=rating.rating,
            review=rating.review,
            rated_at=rating.rated_at
        )
        for movie, rating in results
    ]
    
    return PaginatedRatingsResponse(
        ratings=ratings,
        total=total_count,
        skip=skip,
        limit=limit
    )

@router.get("/stats", response_model=MovieStats)
async def get_rating_stats(db: Session = Depends(get_db)):
    """Get overall statistics about user ratings"""
    from sqlalchemy import func
    
    stats = db.query(
        func.count(UserRating.id).label("total_ratings"),
        func.avg(UserRating.rating).label("average_rating"),
        func.min(UserRating.rating).label("min_rating"),
        func.max(UserRating.rating).label("max_rating"),
        func.count(func.distinct(Movie.year)).label("unique_years"),
        func.min(Movie.year).label("earliest_year"),
        func.max(Movie.year).label("latest_year")
    ).join(Movie).first()
    
    return MovieStats(
        total_ratings=stats.total_ratings or 0,
        average_rating=round(stats.average_rating or 0, 2),
        min_rating=stats.min_rating or 0,
        max_rating=stats.max_rating or 0,
        unique_years=stats.unique_years or 0,
        earliest_year=stats.earliest_year or 0,
        latest_year=stats.latest_year or 0
    )

@router.get("/genres", response_model=List[str])
async def get_available_genres(db: Session = Depends(get_db)):
    """Get all unique genres from the movie collection"""
    # Get all genres from all movies
    movies_with_genres = db.query(Movie.genres).filter(Movie.genres.isnot(None)).all()
    
    # Flatten the list of genre lists and get unique values
    all_genres = set()
    for movie_genres in movies_with_genres:
        if movie_genres[0]:  # Check if genres is not None
            all_genres.update(movie_genres[0])
    
    return sorted(list(all_genres))

@router.get("/{imdb_id}", response_model=RatingResponse)
async def get_movie_rating(imdb_id: str, db: Session = Depends(get_db)):
    """Get a specific movie rating by IMDB ID"""
    result = db.query(Movie, UserRating).join(UserRating).filter(Movie.imdb_id == imdb_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Movie rating not found")
    
    movie, rating = result
    return RatingResponse(
        movie=MovieResponse.from_orm(movie),
        rating=rating.rating,
        review=rating.review,
        rated_at=rating.rated_at
    )