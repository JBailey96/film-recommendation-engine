from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    imdb_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    original_title = Column(String)  # For international films
    title_type = Column(String)  # Movie, TV Movie, Video, etc.
    year = Column(Integer)
    release_date = Column(DateTime(timezone=True))  # Official release date
    runtime_minutes = Column(Integer)
    genres = Column(JSON)  # Store as list of strings
    director = Column(String)
    plot = Column(Text)
    poster_url = Column(String)
    imdb_rating = Column(Float)
    imdb_votes = Column(Integer)
    box_office = Column(String)
    country = Column(String)
    language = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_rating = relationship("UserRating", back_populates="movie", uselist=False)
    cast_members = relationship("CastMember", back_populates="movie")
    poster_analysis = relationship("PosterAnalysis", back_populates="movie", uselist=False)

class UserRating(Base):
    __tablename__ = "user_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-10 scale
    review = Column(Text)
    rated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    movie = relationship("Movie", back_populates="user_rating")

class CastMember(Base):
    __tablename__ = "cast_members"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String)  # "actor", "director", "writer", etc.
    character = Column(String)  # For actors
    
    # Relationships
    movie = relationship("Movie", back_populates="cast_members")

class PosterAnalysis(Base):
    __tablename__ = "poster_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    dominant_colors = Column(JSON)  # RGB values
    color_palette = Column(JSON)
    brightness_score = Column(Float)
    contrast_score = Column(Float)
    text_ratio = Column(Float)  # Percentage of poster that is text
    face_count = Column(Integer)
    style_tags = Column(JSON)  # ["dark", "colorful", "minimalist", etc.]
    claude_analysis = Column(Text)  # LLM analysis of poster style
    
    # Relationships
    movie = relationship("Movie", back_populates="poster_analysis")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, nullable=False)  # "genre", "year", "runtime", etc.
    analysis_data = Column(JSON, nullable=False)
    insights = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScrapingStatus(Base):
    __tablename__ = "scraping_status"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)  # "pending", "running", "completed", "failed"
    total_ratings = Column(Integer)
    scraped_ratings = Column(Integer, default=0)
    current_movie = Column(String)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String)  # User-defined title for saved conversations
    is_saved = Column(Boolean, default=False)  # Whether the conversation is saved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("chat_conversations.conversation_id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")