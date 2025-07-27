import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any
from collections import Counter
import json
from datetime import datetime

from ..database.models import Movie, UserRating, CastMember, UserPreferences
from ..schemas.analysis import (
    GenreAnalysis, GenreData, YearAnalysis, YearData, DecadeData,
    RuntimeAnalysis, RuntimeData, CastAnalysis, PersonData, OverallInsights
)

class PreferenceAnalyzer:
    def __init__(self, db: Session, claude_api_key: str = None):
        self.db = db
        self.claude_api_key = claude_api_key
    
    async def analyze_genres(self, force_regenerate: bool = False) -> GenreAnalysis:
        """Analyze user's genre preferences"""
        
        # Check if analysis already exists
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "genres"
            ).first()
            if existing:
                return GenreAnalysis(**existing.analysis_data)
        
        # Get all ratings with genres
        query = self.db.query(Movie, UserRating).join(UserRating).filter(
            Movie.genres.isnot(None)
        )
        results = query.all()
        
        if not results:
            return GenreAnalysis(
                favorite_genres=[], least_favorite_genres=[], 
                genre_distribution={}, insights="No data available"
            )
        
        # Flatten genres and calculate statistics
        genre_stats = {}
        all_genres = []
        
        for movie, rating in results:
            if movie.genres:
                for genre in movie.genres:
                    all_genres.append(genre)
                    if genre not in genre_stats:
                        genre_stats[genre] = {'ratings': [], 'count': 0}
                    genre_stats[genre]['ratings'].append(rating.rating)
                    genre_stats[genre]['count'] += 1
        
        # Calculate average ratings and percentages
        total_ratings = len(results)
        genre_data = []
        
        for genre, stats in genre_stats.items():
            avg_rating = np.mean(stats['ratings'])
            percentage = (stats['count'] / total_ratings) * 100
            
            genre_data.append(GenreData(
                genre=genre,
                count=stats['count'],
                average_rating=round(avg_rating, 2),
                percentage=round(percentage, 2)
            ))
        
        # Sort by average rating
        genre_data.sort(key=lambda x: x.average_rating, reverse=True)
        
        # Get favorites (top 5) and least favorites (bottom 5)
        favorite_genres = genre_data[:5]
        least_favorite_genres = genre_data[-5:][::-1]  # Reverse for lowest first
        
        # Genre distribution
        genre_distribution = dict(Counter(all_genres))
        
        # Generate insights
        insights = self._generate_genre_insights(genre_data, total_ratings)
        
        analysis = GenreAnalysis(
            favorite_genres=favorite_genres,
            least_favorite_genres=least_favorite_genres,
            genre_distribution=genre_distribution,
            insights=insights
        )
        
        # Save analysis
        self._save_analysis("genres", analysis.dict())
        
        return analysis
    
    async def analyze_years(self, force_regenerate: bool = False) -> YearAnalysis:
        """Analyze user's year/decade preferences"""
        
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "years"
            ).first()
            if existing:
                return YearAnalysis(**existing.analysis_data)
        
        query = self.db.query(Movie, UserRating).join(UserRating).filter(
            Movie.year.isnot(None)
        )
        results = query.all()
        
        if not results:
            return YearAnalysis(
                year_distribution=[], decade_preferences=[], 
                favorite_decades=[], insights="No data available"
            )
        
        # Year analysis
        year_stats = {}
        for movie, rating in results:
            year = movie.year
            if year not in year_stats:
                year_stats[year] = {'ratings': [], 'count': 0}
            year_stats[year]['ratings'].append(rating.rating)
            year_stats[year]['count'] += 1
        
        year_data = []
        for year, stats in year_stats.items():
            year_data.append(YearData(
                year=year,
                count=stats['count'],
                average_rating=round(np.mean(stats['ratings']), 2)
            ))
        
        year_data.sort(key=lambda x: x.year)
        
        # Decade analysis
        decade_stats = {}
        total_movies = len(results)
        
        for movie, rating in results:
            decade = (movie.year // 10) * 10
            decade_str = f"{decade}s"
            
            if decade_str not in decade_stats:
                decade_stats[decade_str] = {'ratings': [], 'count': 0}
            decade_stats[decade_str]['ratings'].append(rating.rating)
            decade_stats[decade_str]['count'] += 1
        
        decade_data = []
        for decade, stats in decade_stats.items():
            decade_data.append(DecadeData(
                decade=decade,
                count=stats['count'],
                average_rating=round(np.mean(stats['ratings']), 2),
                percentage=round((stats['count'] / total_movies) * 100, 2)
            ))
        
        decade_data.sort(key=lambda x: x.average_rating, reverse=True)
        favorite_decades = [d.decade for d in decade_data[:3]]
        
        insights = self._generate_year_insights(decade_data, year_data)
        
        analysis = YearAnalysis(
            year_distribution=year_data,
            decade_preferences=decade_data,
            favorite_decades=favorite_decades,
            insights=insights
        )
        
        self._save_analysis("years", analysis.dict())
        return analysis
    
    async def analyze_runtime(self, force_regenerate: bool = False) -> RuntimeAnalysis:
        """Analyze user's runtime preferences"""
        
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "runtime"
            ).first()
            if existing:
                return RuntimeAnalysis(**existing.analysis_data)
        
        query = self.db.query(Movie, UserRating).join(UserRating).filter(
            Movie.runtime_minutes.isnot(None)
        )
        results = query.all()
        
        if not results:
            return RuntimeAnalysis(
                runtime_distribution=[], preferred_length="Unknown",
                average_runtime=0, insights="No data available"
            )
        
        # Categorize by runtime
        runtime_categories = {
            "Short (< 90 min)": (0, 89),
            "Standard (90-119 min)": (90, 119),
            "Long (120-149 min)": (120, 149),
            "Epic (150+ min)": (150, 999)
        }
        
        runtime_stats = {cat: {'ratings': [], 'count': 0} for cat in runtime_categories}
        runtimes = []
        
        for movie, rating in results:
            runtime = movie.runtime_minutes
            runtimes.append(runtime)
            
            for category, (min_time, max_time) in runtime_categories.items():
                if min_time <= runtime <= max_time:
                    runtime_stats[category]['ratings'].append(rating.rating)
                    runtime_stats[category]['count'] += 1
                    break
        
        total_movies = len(results)
        runtime_data = []
        
        for category, stats in runtime_stats.items():
            if stats['count'] > 0:
                runtime_data.append(RuntimeData(
                    runtime_range=category,
                    count=stats['count'],
                    average_rating=round(np.mean(stats['ratings']), 2),
                    percentage=round((stats['count'] / total_movies) * 100, 2)
                ))
        
        runtime_data.sort(key=lambda x: x.average_rating, reverse=True)
        preferred_length = runtime_data[0].runtime_range if runtime_data else "Unknown"
        average_runtime = round(np.mean(runtimes), 1)
        
        insights = self._generate_runtime_insights(runtime_data, average_runtime)
        
        analysis = RuntimeAnalysis(
            runtime_distribution=runtime_data,
            preferred_length=preferred_length,
            average_runtime=average_runtime,
            insights=insights
        )
        
        self._save_analysis("runtime", analysis.dict())
        return analysis
    
    async def analyze_cast(self, force_regenerate: bool = False) -> CastAnalysis:
        """Analyze user's favorite actors and directors"""
        
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "cast"
            ).first()
            if existing:
                return CastAnalysis(**existing.analysis_data)
        
        # Get actors
        actor_query = self.db.query(CastMember, UserRating, Movie).join(
            Movie, CastMember.movie_id == Movie.id
        ).join(UserRating, Movie.id == UserRating.movie_id).filter(
            CastMember.role == "actor"
        )
        
        actor_results = actor_query.all()
        actor_stats = {}
        
        for cast_member, rating, movie in actor_results:
            name = cast_member.name
            if name not in actor_stats:
                actor_stats[name] = {'ratings': [], 'movies': []}
            actor_stats[name]['ratings'].append(rating.rating)
            actor_stats[name]['movies'].append(movie.title)
        
        # Filter actors with at least 2 movies
        actor_data = []
        for name, stats in actor_stats.items():
            if len(stats['ratings']) >= 2:
                actor_data.append(PersonData(
                    name=name,
                    count=len(stats['ratings']),
                    average_rating=round(np.mean(stats['ratings']), 2),
                    movies=stats['movies'][:5]  # Limit to 5 movies
                ))
        
        actor_data.sort(key=lambda x: (x.average_rating, x.count), reverse=True)
        favorite_actors = actor_data[:10]
        
        # Get directors
        director_stats = {}
        for movie, rating in self.db.query(Movie, UserRating).join(UserRating).filter(
            Movie.director.isnot(None)
        ):
            director = movie.director
            if director not in director_stats:
                director_stats[director] = {'ratings': [], 'movies': []}
            director_stats[director]['ratings'].append(rating.rating)
            director_stats[director]['movies'].append(movie.title)
        
        director_data = []
        for name, stats in director_stats.items():
            if len(stats['ratings']) >= 2:
                director_data.append(PersonData(
                    name=name,
                    count=len(stats['ratings']),
                    average_rating=round(np.mean(stats['ratings']), 2),
                    movies=stats['movies'][:5]
                ))
        
        director_data.sort(key=lambda x: (x.average_rating, x.count), reverse=True)
        favorite_directors = director_data[:10]
        
        actor_insights = self._generate_cast_insights(favorite_actors, "actors")
        director_insights = self._generate_cast_insights(favorite_directors, "directors")
        
        analysis = CastAnalysis(
            favorite_actors=favorite_actors,
            favorite_directors=favorite_directors,
            actor_insights=actor_insights,
            director_insights=director_insights
        )
        
        self._save_analysis("cast", analysis.dict())
        return analysis
    
    async def generate_overall_insights(self, force_regenerate: bool = False) -> OverallInsights:
        """Generate comprehensive insights using Claude API"""
        
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "overall_insights"
            ).first()
            if existing:
                return OverallInsights(**existing.analysis_data)
        
        # Gather all analysis data
        genre_analysis = await self.analyze_genres()
        year_analysis = await self.analyze_years()
        runtime_analysis = await self.analyze_runtime()
        cast_analysis = await self.analyze_cast()
        
        # Prepare data for Claude
        analysis_summary = {
            "genres": {
                "favorites": [g.genre for g in genre_analysis.favorite_genres[:3]],
                "least_favorites": [g.genre for g in genre_analysis.least_favorite_genres[:3]]
            },
            "decades": {
                "favorites": year_analysis.favorite_decades[:3]
            },
            "runtime": {
                "preferred": runtime_analysis.preferred_length,
                "average": runtime_analysis.average_runtime
            },
            "cast": {
                "favorite_actors": [a.name for a in cast_analysis.favorite_actors[:5]],
                "favorite_directors": [d.name for d in cast_analysis.favorite_directors[:5]]
            }
        }
        
        # Generate Claude analysis if API key available
        claude_analysis = ""
        if self.claude_api_key:
            claude_analysis = await self._generate_claude_insights(analysis_summary)
        
        insights = OverallInsights(
            personality_profile=self._generate_personality_profile(analysis_summary),
            viewing_patterns=self._generate_viewing_patterns(analysis_summary),
            recommendations=self._generate_recommendations_list(analysis_summary),
            key_preferences=analysis_summary,
            claude_analysis=claude_analysis
        )
        
        self._save_analysis("overall_insights", insights.dict())
        return insights
    
    def _generate_genre_insights(self, genre_data: List[GenreData], total_ratings: int) -> str:
        """Generate insights about genre preferences"""
        if not genre_data:
            return "No genre data available."
        
        top_genre = genre_data[0]
        insights = [
            f"Your highest-rated genre is {top_genre.genre} with an average rating of {top_genre.average_rating}/10.",
            f"You've rated {total_ratings} movies across {len(genre_data)} different genres."
        ]
        
        # Find genre diversity
        if len(genre_data) > 5:
            insights.append("You enjoy a diverse range of genres.")
        else:
            insights.append("You tend to stick to a smaller set of preferred genres.")
        
        return " ".join(insights)
    
    def _generate_year_insights(self, decade_data: List[DecadeData], year_data: List[YearData]) -> str:
        """Generate insights about year/decade preferences"""
        if not decade_data:
            return "No year data available."
        
        favorite_decade = decade_data[0]
        insights = [
            f"Your favorite decade is the {favorite_decade.decade} with an average rating of {favorite_decade.average_rating}/10.",
            f"This represents {favorite_decade.percentage}% of your rated movies."
        ]
        
        return " ".join(insights)
    
    def _generate_runtime_insights(self, runtime_data: List[RuntimeData], average_runtime: float) -> str:
        """Generate insights about runtime preferences"""
        if not runtime_data:
            return "No runtime data available."
        
        preferred = runtime_data[0]
        insights = [
            f"You prefer {preferred.runtime_range.lower()} movies, rating them {preferred.average_rating}/10 on average.",
            f"Your average movie runtime is {average_runtime} minutes."
        ]
        
        return " ".join(insights)
    
    def _generate_cast_insights(self, person_data: List[PersonData], role: str) -> str:
        """Generate insights about cast preferences"""
        if not person_data:
            return f"No {role} data available."
        
        top_person = person_data[0]
        insights = [
            f"Your favorite {role[:-1]} is {top_person.name} with an average rating of {top_person.average_rating}/10 across {top_person.count} movies."
        ]
        
        return " ".join(insights)
    
    def _generate_personality_profile(self, data: Dict) -> str:
        """Generate a personality profile based on preferences"""
        profile_parts = []
        
        if data["genres"]["favorites"]:
            top_genres = ", ".join(data["genres"]["favorites"])
            profile_parts.append(f"You gravitate towards {top_genres} films")
        
        if data["runtime"]["preferred"]:
            profile_parts.append(f"prefer {data['runtime']['preferred'].lower()} movies")
        
        return ". ".join(profile_parts) + "."
    
    def _generate_viewing_patterns(self, data: Dict) -> str:
        """Generate viewing pattern insights"""
        patterns = []
        
        if data["decades"]["favorites"]:
            fav_decade = data["decades"]["favorites"][0]
            patterns.append(f"You show a strong preference for {fav_decade} cinema")
        
        return ". ".join(patterns) + "." if patterns else "No clear viewing patterns identified."
    
    def _generate_recommendations_list(self, data: Dict) -> List[str]:
        """Generate recommendation categories"""
        recommendations = []
        
        if data["genres"]["favorites"]:
            top_genre = data["genres"]["favorites"][0]
            recommendations.append(f"More {top_genre} films")
        
        if data["cast"]["favorite_directors"]:
            top_director = data["cast"]["favorite_directors"][0]
            recommendations.append(f"Films by {top_director}")
        
        return recommendations[:5]
    
    async def _generate_claude_insights(self, analysis_summary: Dict) -> str:
        """Generate insights using Claude API"""
        if not self.claude_api_key:
            return ""
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.claude_api_key)
            
            prompt = f"""
            Based on this user's movie rating data, provide deep insights about their movie preferences and personality:
            
            {json.dumps(analysis_summary, indent=2)}
            
            Please provide:
            1. A personality profile based on their movie preferences
            2. Hidden patterns in their viewing habits
            3. Recommendations for exploration
            4. What their preferences reveal about their personality
            
            Keep the response concise but insightful.
            """
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating Claude insights: {e}")
            return "Claude analysis unavailable."
    
    def _save_analysis(self, analysis_type: str, data: Dict):
        """Save analysis to database"""
        existing = self.db.query(UserPreferences).filter(
            UserPreferences.analysis_type == analysis_type
        ).first()
        
        if existing:
            existing.analysis_data = data
            existing.created_at = datetime.utcnow()
        else:
            analysis = UserPreferences(
                analysis_type=analysis_type,
                analysis_data=data
            )
            self.db.add(analysis)
        
        self.db.commit()