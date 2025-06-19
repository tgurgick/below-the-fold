from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

ALLOWED_SOURCES = {
    "The Verge",
    "TechCrunch",
    "Wired",
    "MIT Technology Review",
    "The New York Times",
    "Financial Times",
    "Nature",
    "Science",
    "Reuters",
    "Bloomberg",
    "CNBC",
    "Wall Street Journal"
}

class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str
    url: str
    published_at: datetime
    category: str
    importance_score: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)
    why_it_matters: str

    @validator('source')
    def validate_source(cls, v):
        if v not in ALLOWED_SOURCES:
            raise ValueError(f"Source must be one of: {', '.join(sorted(ALLOWED_SOURCES))}")
        return v

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_articles: int
    timestamp: datetime 