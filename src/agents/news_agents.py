from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging
from src.agents.perplexity_agent import PerplexityAgent
from src.models.news import NewsArticle, NewsResponse

logger = logging.getLogger(__name__)

class BaseNewsAgent:
    """Base class for all news agents"""
    def __init__(self, perplexity_agent: PerplexityAgent):
        self.perplexity_agent = perplexity_agent
        self.last_update = None
        self.cached_articles = []

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch news articles - to be implemented by subclasses"""
        raise NotImplementedError

    def get_cached_articles(self) -> List[NewsArticle]:
        """Get cached articles if they're still fresh"""
        if self.last_update and datetime.now(timezone.utc) - self.last_update < timedelta(minutes=5):
            return self.cached_articles
        return []

class BreakingNewsAgent(BaseNewsAgent):
    """Agent for latest breaking news (last 24 hours)"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            response = await self.perplexity_agent.get_top_news(
                num_articles=10,
                prompt_key='breaking_news'
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            return response.articles
        except Exception as e:
            logger.error(f"Error fetching breaking news: {str(e)}")
            return []

class TopStoriesAgent(BaseNewsAgent):
    """Agent for top stories (last 7 days)"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            response = await self.perplexity_agent.get_top_news(
                num_articles=10,
                prompt_key='top_stories'
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            return response.articles
        except Exception as e:
            logger.error(f"Error fetching top stories: {str(e)}")
            return []

class FundingAgent(BaseNewsAgent):
    """Agent for funding and M&A news"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            response = await self.perplexity_agent.get_top_news(
                num_articles=5,
                prompt_key='funding_news',
                categories=['funding', 'acquisition', 'merger']
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            return response.articles
        except Exception as e:
            logger.error(f"Error fetching funding news: {str(e)}")
            return []

class ResearchAgent(BaseNewsAgent):
    """Agent for research and technical breakthroughs"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            response = await self.perplexity_agent.get_top_news(
                num_articles=5,
                prompt_key='research_news',
                categories=['research', 'breakthrough', 'technical']
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            return response.articles
        except Exception as e:
            logger.error(f"Error fetching research news: {str(e)}")
            return []

class Newsroom:
    """Coordinates all news agents and manages updates"""
    def __init__(self, perplexity_agent: PerplexityAgent):
        self.breaking_news = BreakingNewsAgent(perplexity_agent)
        self.top_stories = TopStoriesAgent(perplexity_agent)
        self.funding = FundingAgent(perplexity_agent)
        self.research = ResearchAgent(perplexity_agent)
        self.last_full_update = None

    async def update_all(self) -> Dict[str, List[NewsArticle]]:
        """Update all news categories"""
        try:
            logger.info("Starting full newsroom update")
            
            # Fetch all categories in parallel
            breaking_news = await self.breaking_news.fetch_news()
            top_stories = await self.top_stories.fetch_news()
            funding_news = await self.funding.fetch_news()
            research_news = await self.research.fetch_news()
            
            self.last_full_update = datetime.now(timezone.utc)
            
            return {
                "breaking_news": breaking_news,
                "top_stories": top_stories,
                "funding_news": funding_news,
                "research_news": research_news
            }
        except Exception as e:
            logger.error(f"Error in newsroom update: {str(e)}")
            return {}

    def get_cached_news(self) -> Dict[str, List[NewsArticle]]:
        """Get cached news from all agents"""
        return {
            "breaking_news": self.breaking_news.get_cached_articles(),
            "top_stories": self.top_stories.get_cached_articles(),
            "funding_news": self.funding.get_cached_articles(),
            "research_news": self.research.get_cached_articles()
        }

    def needs_update(self) -> bool:
        """Check if news needs updating"""
        if not self.last_full_update:
            return True
        return datetime.now(timezone.utc) - self.last_full_update > timedelta(minutes=5) 