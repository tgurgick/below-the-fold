from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_articles: int
    timestamp: datetime 