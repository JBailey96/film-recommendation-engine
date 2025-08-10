import asyncio
import aiohttp
import numpy as np
from PIL import Image, ImageStat
import io
import colorsys
import os
from collections import Counter
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Tuple
import json

from ..database.models import Movie, UserRating, PosterAnalysis, UserPreferences
from ..schemas.analysis import PosterStyleAnalysis, ColorData, StyleData

class PosterAnalyzer:
    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude_api_key = claude_api_key or os.getenv("CLAUDE_API_KEY")
    
    async def analyze_movie_poster(self, movie_id: int, poster_url: str):
        """Analyze a single movie poster"""
        try:
            # Download and analyze poster
            poster_data = await self._download_poster(poster_url)
            if not poster_data:
                return
            
            image = Image.open(io.BytesIO(poster_data))
            
            # Perform visual analysis
            analysis = {
                'dominant_colors': self._extract_dominant_colors(image),
                'color_palette': self._extract_color_palette(image),
                'brightness_score': self._calculate_brightness(image),
                'contrast_score': self._calculate_contrast(image),
                'text_ratio': self._estimate_text_ratio(image),
                'face_count': 0,  # Placeholder - would need face detection
                'style_tags': self._classify_poster_style(image)
            }
            
            # Claude analysis if API key available
            claude_analysis = ""
            if self.claude_api_key:
                claude_analysis = await self._analyze_poster_with_claude(poster_url, analysis)
            
            # Save to database
            poster_analysis = PosterAnalysis(
                movie_id=movie_id,
                dominant_colors=analysis['dominant_colors'],
                color_palette=analysis['color_palette'],
                brightness_score=analysis['brightness_score'],
                contrast_score=analysis['contrast_score'],
                text_ratio=analysis['text_ratio'],
                face_count=analysis['face_count'],
                style_tags=analysis['style_tags'],
                claude_analysis=claude_analysis
            )
            
            self.db.add(poster_analysis)
            self.db.commit()
            
        except Exception as e:
            print(f"Error analyzing poster for movie {movie_id}: {e}")
    
    async def analyze_poster_styles(self, force_regenerate: bool = False) -> PosterStyleAnalysis:
        """Analyze overall poster style preferences"""
        
        if not force_regenerate:
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.analysis_type == "poster_styles"
            ).first()
            if existing:
                return PosterStyleAnalysis(**existing.analysis_data)
        
        # Get all poster analyses with user ratings
        query = self.db.query(PosterAnalysis, UserRating, Movie).join(
            Movie, PosterAnalysis.movie_id == Movie.id
        ).join(UserRating, Movie.id == UserRating.movie_id)
        
        results = query.all()
        
        if not results:
            return PosterStyleAnalysis(
                dominant_colors=[], style_preferences=[], 
                brightness_preference="Unknown", contrast_preference="Unknown",
                insights="No poster data available", claude_analysis=""
            )
        
        # Analyze color preferences
        color_data = self._analyze_color_preferences(results)
        
        # Analyze style preferences
        style_data = self._analyze_style_preferences(results)
        
        # Analyze brightness and contrast preferences
        brightness_pref = self._analyze_brightness_preference(results)
        contrast_pref = self._analyze_contrast_preference(results)
        
        # Generate insights
        insights = self._generate_poster_insights(color_data, style_data, brightness_pref, contrast_pref)
        
        # Claude analysis of overall poster preferences
        claude_analysis = ""
        if self.claude_api_key:
            claude_analysis = await self._generate_poster_claude_analysis(
                color_data, style_data, brightness_pref, contrast_pref
            )
        
        analysis = PosterStyleAnalysis(
            dominant_colors=color_data,
            style_preferences=style_data,
            brightness_preference=brightness_pref,
            contrast_preference=contrast_pref,
            insights=insights,
            claude_analysis=claude_analysis
        )
        
        # Save analysis
        self._save_poster_analysis(analysis.dict())
        
        return analysis
    
    async def _download_poster(self, url: str) -> Optional[bytes]:
        """Download poster image"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"Error downloading poster {url}: {e}")
        return None
    
    def _extract_dominant_colors(self, image: Image.Image, num_colors: int = 5) -> List[List[int]]:
        """Extract dominant colors from image"""
        try:
            # Convert to RGB and resize for performance
            image = image.convert('RGB')
            image = image.resize((150, 150))
            
            # Get all pixels
            pixels = list(image.getdata())
            
            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            colors = kmeans.cluster_centers_.astype(int).tolist()
            return colors
            
        except Exception as e:
            print(f"Error extracting dominant colors: {e}")
            return []
    
    def _extract_color_palette(self, image: Image.Image) -> List[str]:
        """Extract color palette as hex values"""
        try:
            dominant_colors = self._extract_dominant_colors(image)
            palette = []
            
            for color in dominant_colors:
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                palette.append(hex_color)
            
            return palette
            
        except Exception as e:
            print(f"Error extracting color palette: {e}")
            return []
    
    def _calculate_brightness(self, image: Image.Image) -> float:
        """Calculate average brightness of image"""
        try:
            grayscale = image.convert('L')
            stat = ImageStat.Stat(grayscale)
            return stat.mean[0] / 255.0  # Normalize to 0-1
        except Exception as e:
            print(f"Error calculating brightness: {e}")
            return 0.5
    
    def _calculate_contrast(self, image: Image.Image) -> float:
        """Calculate contrast of image"""
        try:
            grayscale = image.convert('L')
            stat = ImageStat.Stat(grayscale)
            return stat.stddev[0] / 128.0  # Normalize to 0-1
        except Exception as e:
            print(f"Error calculating contrast: {e}")
            return 0.5
    
    def _estimate_text_ratio(self, image: Image.Image) -> float:
        """Estimate the ratio of text in the image (simplified)"""
        try:
            # This is a simplified estimation
            # In a real implementation, you'd use OCR or edge detection
            grayscale = image.convert('L')
            
            # Convert to numpy array
            img_array = np.array(grayscale)
            
            # Simple edge detection using gradients
            grad_x = np.gradient(img_array, axis=1)
            grad_y = np.gradient(img_array, axis=0)
            edges = np.sqrt(grad_x**2 + grad_y**2)
            
            # High edge density might indicate text
            edge_ratio = np.sum(edges > 20) / img_array.size
            
            return min(edge_ratio * 2, 1.0)  # Scale and cap at 1.0
            
        except Exception as e:
            print(f"Error estimating text ratio: {e}")
            return 0.3
    
    def _classify_poster_style(self, image: Image.Image) -> List[str]:
        """Classify poster style based on visual features"""
        try:
            styles = []
            
            brightness = self._calculate_brightness(image)
            contrast = self._calculate_contrast(image)
            
            # Classify based on brightness
            if brightness < 0.3:
                styles.append("dark")
            elif brightness > 0.7:
                styles.append("bright")
            else:
                styles.append("balanced")
            
            # Classify based on contrast
            if contrast > 0.6:
                styles.append("high-contrast")
            elif contrast < 0.3:
                styles.append("low-contrast")
            else:
                styles.append("medium-contrast")
            
            # Color analysis
            dominant_colors = self._extract_dominant_colors(image, 3)
            if dominant_colors:
                # Check for colorfulness
                color_variance = np.var([np.var(color) for color in dominant_colors])
                if color_variance > 1000:
                    styles.append("colorful")
                else:
                    styles.append("muted")
            
            return styles
            
        except Exception as e:
            print(f"Error classifying poster style: {e}")
            return ["unknown"]
    
    def _analyze_color_preferences(self, results) -> List[ColorData]:
        """Analyze user's color preferences based on ratings"""
        color_stats = {}
        
        for poster_analysis, rating, movie in results:
            if poster_analysis.dominant_colors:
                for color_rgb in poster_analysis.dominant_colors:
                    # Convert to color name (simplified)
                    color_name = self._rgb_to_color_name(color_rgb)
                    
                    if color_name not in color_stats:
                        color_stats[color_name] = {
                            'rgb_values': color_rgb,
                            'ratings': [],
                            'count': 0
                        }
                    
                    color_stats[color_name]['ratings'].append(rating.rating)
                    color_stats[color_name]['count'] += 1
        
        color_data = []
        for color_name, stats in color_stats.items():
            if stats['count'] >= 2:  # Only include colors that appear multiple times
                color_data.append(ColorData(
                    color_name=color_name,
                    rgb_values=stats['rgb_values'],
                    frequency=stats['count'],
                    average_rating=round(np.mean(stats['ratings']), 2)
                ))
        
        color_data.sort(key=lambda x: x.average_rating, reverse=True)
        return color_data[:10]
    
    def _analyze_style_preferences(self, results) -> List[StyleData]:
        """Analyze user's style preferences"""
        style_stats = {}
        total_movies = len(results)
        
        for poster_analysis, rating, movie in results:
            if poster_analysis.style_tags:
                for style in poster_analysis.style_tags:
                    if style not in style_stats:
                        style_stats[style] = {'ratings': [], 'count': 0}
                    
                    style_stats[style]['ratings'].append(rating.rating)
                    style_stats[style]['count'] += 1
        
        style_data = []
        for style, stats in style_stats.items():
            if stats['count'] >= 2:
                style_data.append(StyleData(
                    style=style,
                    count=stats['count'],
                    average_rating=round(np.mean(stats['ratings']), 2),
                    percentage=round((stats['count'] / total_movies) * 100, 2)
                ))
        
        style_data.sort(key=lambda x: x.average_rating, reverse=True)
        return style_data[:10]
    
    def _analyze_brightness_preference(self, results) -> str:
        """Analyze brightness preference"""
        brightness_categories = {"dark": [], "medium": [], "bright": []}
        
        for poster_analysis, rating, movie in results:
            if poster_analysis.brightness_score is not None:
                brightness = poster_analysis.brightness_score
                if brightness < 0.33:
                    brightness_categories["dark"].append(rating.rating)
                elif brightness > 0.66:
                    brightness_categories["bright"].append(rating.rating)
                else:
                    brightness_categories["medium"].append(rating.rating)
        
        # Find category with highest average rating
        best_category = "medium"
        best_rating = 0
        
        for category, ratings in brightness_categories.items():
            if ratings:
                avg_rating = np.mean(ratings)
                if avg_rating > best_rating:
                    best_rating = avg_rating
                    best_category = category
        
        return best_category
    
    def _analyze_contrast_preference(self, results) -> str:
        """Analyze contrast preference"""
        contrast_categories = {"low": [], "medium": [], "high": []}
        
        for poster_analysis, rating, movie in results:
            if poster_analysis.contrast_score is not None:
                contrast = poster_analysis.contrast_score
                if contrast < 0.33:
                    contrast_categories["low"].append(rating.rating)
                elif contrast > 0.66:
                    contrast_categories["high"].append(rating.rating)
                else:
                    contrast_categories["medium"].append(rating.rating)
        
        # Find category with highest average rating
        best_category = "medium"
        best_rating = 0
        
        for category, ratings in contrast_categories.items():
            if ratings:
                avg_rating = np.mean(ratings)
                if avg_rating > best_rating:
                    best_rating = avg_rating
                    best_category = category
        
        return best_category
    
    def _rgb_to_color_name(self, rgb: List[int]) -> str:
        """Convert RGB to basic color name"""
        r, g, b = rgb
        
        # Simple color classification
        if r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > max(g, b) + 50:
            return "red"
        elif g > max(r, b) + 50:
            return "green"
        elif b > max(r, g) + 50:
            return "blue"
        elif r > 150 and g > 150 and b < 100:
            return "yellow"
        elif r > 150 and g < 100 and b > 150:
            return "purple"
        elif r < 100 and g > 150 and b > 150:
            return "cyan"
        elif r > 150 and g > 100 and b < 100:
            return "orange"
        else:
            return "neutral"
    
    def _generate_poster_insights(self, color_data, style_data, brightness_pref, contrast_pref) -> str:
        """Generate insights about poster preferences"""
        insights = []
        
        if color_data:
            top_color = color_data[0]
            insights.append(f"Your highest-rated poster color is {top_color.color_name} with an average rating of {top_color.average_rating}/10.")
        
        if style_data:
            top_style = style_data[0]
            insights.append(f"You prefer {top_style.style} poster styles.")
        
        insights.append(f"You tend to prefer {brightness_pref} brightness and {contrast_pref} contrast in movie posters.")
        
        return " ".join(insights)
    
    async def _analyze_poster_with_claude(self, poster_url: str, visual_analysis: Dict) -> str:
        """Analyze poster style using Claude API"""
        if not self.claude_api_key:
            return ""
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.claude_api_key)
            
            prompt = f"""
            Analyze this movie poster and describe its visual style, mood, and design elements:
            
            Poster URL: {poster_url}
            Technical analysis: {json.dumps(visual_analysis, indent=2)}
            
            Please describe:
            1. The overall artistic style
            2. Color scheme and mood
            3. Typography and layout
            4. Genre indicators
            5. Target audience appeal
            
            Keep the response concise but detailed.
            """
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error analyzing poster with Claude: {e}")
            return ""
    
    async def _generate_poster_claude_analysis(self, color_data, style_data, brightness_pref, contrast_pref) -> str:
        """Generate overall poster preference analysis using Claude"""
        if not self.claude_api_key:
            return ""
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.claude_api_key)
            
            analysis_data = {
                "favorite_colors": [c.color_name for c in color_data[:3]],
                "favorite_styles": [s.style for s in style_data[:3]],
                "brightness_preference": brightness_pref,
                "contrast_preference": contrast_pref
            }
            
            prompt = f"""
            Based on this user's movie poster preferences, provide insights about their visual taste and personality:
            
            {json.dumps(analysis_data, indent=2)}
            
            Please analyze:
            1. What their poster preferences reveal about their personality
            2. Visual patterns and aesthetic tendencies
            3. How their poster taste relates to movie genre preferences
            4. Design elements they're drawn to and why
            
            Keep the response insightful but concise.
            """
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating poster Claude analysis: {e}")
            return ""
    
    def _save_poster_analysis(self, data: Dict):
        """Save poster analysis to database"""
        existing = self.db.query(UserPreferences).filter(
            UserPreferences.analysis_type == "poster_styles"
        ).first()
        
        if existing:
            existing.analysis_data = data
        else:
            analysis = UserPreferences(
                analysis_type="poster_styles",
                analysis_data=data
            )
            self.db.add(analysis)
        
        self.db.commit()