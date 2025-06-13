from pydantic import BaseModel, validator, HttpUrl
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str
    url: str
    published_at: datetime
    category: Optional[str] = None
    importance_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    why_it_matters: Optional[str] = None

    @validator('source')
    def validate_source(cls, v):
        if not v:
            raise ValueError('Source cannot be empty')
        # List of known reputable sources
        reputable_sources = [
            'the verge', 'techcrunch', 'wired', 'mit technology review', 
            'new york times', 'financial times', 'nature', 'science',
            'reuters', 'bloomberg', 'wall street journal', 'washington post',
            'the guardian', 'the economist', 'fortune', 'business insider',
            'cnbc', 'techradar', 'engadget', 'venturebeat', 'zdnet',
            'arstechnica', 'the information', 'protocol', 'axios',
            'btw media'  # Temporarily allow this source for debugging
        ]
        # Check if source contains any of the reputable sources (case insensitive)
        if not any(source in v.lower() for source in reputable_sources):
            logger.warning(f"Source validation failed for: {v}")
            # Temporarily allow any non-empty source for debugging
            return v
        return v

    @validator('url')
    def validate_url(cls, v):
        if not v:
            raise ValueError('URL cannot be empty')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_articles: int
    timestamp: datetime 