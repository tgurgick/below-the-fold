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
        logger.info(f"{self.__class__.__name__}: Initialized")

    async def fetch_news(self) -> List[NewsArticle]:
        """Fetch news articles - to be implemented by subclasses"""
        raise NotImplementedError

    def get_cached_articles(self) -> List[NewsArticle]:
        """Get cached articles if they're still fresh"""
        if self.last_update and datetime.now(timezone.utc) - self.last_update < timedelta(minutes=5):
            logger.info(f"{self.__class__.__name__}: Returning {len(self.cached_articles)} cached articles (fresh)")
            return self.cached_articles
        logger.info(f"{self.__class__.__name__}: Cache expired or empty, need fresh data")
        return []

class BreakingNewsAgent(BaseNewsAgent):
    """Agent for latest breaking news (last 24 hours)"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            logger.info(f"{self.__class__.__name__}: Starting breaking news fetch")
            response = await self.perplexity_agent.get_top_news(
                num_articles=10,
                prompt_key='breaking_news'
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            logger.info(f"{self.__class__.__name__}: Successfully cached {len(self.cached_articles)} breaking news articles")
            return response.articles
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Error fetching breaking news: {str(e)}", exc_info=True)
            return []

class TopStoriesAgent(BaseNewsAgent):
    """Agent for top stories (last 7 days)"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            logger.info(f"{self.__class__.__name__}: Starting top stories fetch")
            response = await self.perplexity_agent.get_top_news(
                num_articles=10,
                prompt_key='top_stories'
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            logger.info(f"{self.__class__.__name__}: Successfully cached {len(self.cached_articles)} top stories")
            return response.articles
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Error fetching top stories: {str(e)}", exc_info=True)
            return []

class FundingAgent(BaseNewsAgent):
    """Agent for funding and M&A news"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            logger.info(f"{self.__class__.__name__}: Starting funding news fetch")
            response = await self.perplexity_agent.get_top_news(
                num_articles=5,
                prompt_key='funding_news',
                categories=['funding', 'acquisition', 'merger']
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            logger.info(f"{self.__class__.__name__}: Successfully cached {len(self.cached_articles)} funding news articles")
            return response.articles
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Error fetching funding news: {str(e)}", exc_info=True)
            return []

class ResearchAgent(BaseNewsAgent):
    """Agent for research and technical breakthroughs"""
    async def fetch_news(self) -> List[NewsArticle]:
        try:
            logger.info(f"{self.__class__.__name__}: Starting research news fetch")
            response = await self.perplexity_agent.get_top_news(
                num_articles=5,
                prompt_key='research_news',
                categories=['research', 'breakthrough', 'technical']
            )
            self.cached_articles = response.articles
            self.last_update = datetime.now(timezone.utc)
            logger.info(f"{self.__class__.__name__}: Successfully cached {len(self.cached_articles)} research news articles")
            return response.articles
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Error fetching research news: {str(e)}", exc_info=True)
            return []

class Newsroom:
    """Coordinates all news agents and manages updates"""
    def __init__(self, perplexity_agent: PerplexityAgent):
        logger.info("Newsroom: Initializing newsroom with all agents")
        self.breaking_news = BreakingNewsAgent(perplexity_agent)
        self.top_stories = TopStoriesAgent(perplexity_agent)
        self.funding = FundingAgent(perplexity_agent)
        self.research = ResearchAgent(perplexity_agent)
        self.last_full_update = None
        logger.info("Newsroom: Successfully initialized all news agents")

    async def update_all(self) -> Dict[str, List[NewsArticle]]:
        """Update all news categories"""
        try:
            logger.info("Newsroom: Starting full newsroom update")
            
            # Fetch all categories in parallel
            logger.info("Newsroom: Fetching breaking news")
            breaking_news = await self.breaking_news.fetch_news()
            
            logger.info("Newsroom: Fetching top stories")
            top_stories = await self.top_stories.fetch_news()
            
            logger.info("Newsroom: Fetching funding news")
            funding_news = await self.funding.fetch_news()
            
            logger.info("Newsroom: Fetching research news")
            research_news = await self.research.fetch_news()
            
            self.last_full_update = datetime.now(timezone.utc)
            
            total_articles = len(breaking_news) + len(top_stories) + len(funding_news) + len(research_news)
            logger.info(f"Newsroom: Full update completed - {total_articles} total articles across all categories")
            
            return {
                "breaking_news": breaking_news,
                "top_stories": top_stories,
                "funding_news": funding_news,
                "research_news": research_news
            }
        except Exception as e:
            logger.error(f"Newsroom: Error in newsroom update: {str(e)}", exc_info=True)
            return {}

    def get_cached_news(self) -> Dict[str, List[NewsArticle]]:
        """Get cached news from all agents"""
        logger.info("Newsroom: Retrieving cached news from all agents")
        cached_news = {
            "breaking_news": self.breaking_news.get_cached_articles(),
            "top_stories": self.top_stories.get_cached_articles(),
            "funding_news": self.funding.get_cached_articles(),
            "research_news": self.research.get_cached_articles()
        }
        
        total_cached = sum(len(articles) for articles in cached_news.values())
        logger.info(f"Newsroom: Retrieved {total_cached} cached articles")
        return cached_news

    def needs_update(self) -> bool:
        """Check if news needs updating"""
        if not self.last_full_update:
            logger.info("Newsroom: No previous update found, update needed")
            return True
        
        time_since_update = datetime.now(timezone.utc) - self.last_full_update
        needs_update = time_since_update > timedelta(minutes=5)
        
        if needs_update:
            logger.info(f"Newsroom: Update needed - {time_since_update.total_seconds()/60:.1f} minutes since last update")
        else:
            logger.info(f"Newsroom: No update needed - {time_since_update.total_seconds()/60:.1f} minutes since last update")
        
        return needs_update 