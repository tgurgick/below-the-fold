import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
logger.debug(f"Loading .env file from: {env_path}")
load_dotenv(env_path, override=True)

# Debug log the API key status
api_key = os.getenv('PERPLEXITY_API_KEY')
logger.debug(f"PERPLEXITY_API_KEY exists: {bool(api_key)}")
logger.debug(f"PERPLEXITY_API_KEY length: {len(api_key) if api_key else 0}")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.news_agents import Newsroom
from src.models.news import NewsResponse
import uvicorn

# Add initial log message
logger.info("API server starting up")

app = FastAPI(
    title="Below the Fold",
    description="An AI-powered news aggregation tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Perplexity agent and newsroom
try:
    perplexity_agent = PerplexityAgent()
    newsroom = Newsroom(perplexity_agent)
    logger.info("Successfully initialized PerplexityAgent and Newsroom")
except ValueError as e:
    logger.error(f"Failed to initialize agents: {str(e)}")
    raise Exception("Failed to initialize news agents. Please check your environment variables.")

@app.on_event("startup")
async def startup_event():
    logger.info("API server startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API server shutting down")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Below the Fold API"}

@app.get("/news/breaking", response_model=NewsResponse)
async def get_breaking_news():
    """Get the latest breaking news from the last 24 hours"""
    try:
        logger.info("API Call: GET /news/breaking")
        articles = await newsroom.breaking_news.fetch_news()
        logger.info(f"Successfully fetched {len(articles)} breaking news articles")
        return NewsResponse(
            articles=articles,
            total_articles=len(articles),
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Error fetching breaking news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching breaking news: {str(e)}"
        )

@app.get("/news/top", response_model=NewsResponse)
async def get_top_stories():
    """Get the most significant stories from the last 7 days"""
    try:
        logger.info("API Call: GET /news/top")
        articles = await newsroom.top_stories.fetch_news()
        logger.info(f"Successfully fetched {len(articles)} top stories")
        return NewsResponse(
            articles=articles,
            total_articles=len(articles),
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Error fetching top stories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching top stories: {str(e)}"
        )

@app.get("/news/funding", response_model=NewsResponse)
async def get_funding_news():
    """Get the latest funding and M&A news"""
    try:
        logger.info("API Call: GET /news/funding")
        articles = await newsroom.funding.fetch_news()
        logger.info(f"Successfully fetched {len(articles)} funding news articles")
        return NewsResponse(
            articles=articles,
            total_articles=len(articles),
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Error fetching funding news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching funding news: {str(e)}"
        )

@app.get("/news/research", response_model=NewsResponse)
async def get_research_news():
    """Get the latest research and technical breakthroughs"""
    try:
        logger.info("API Call: GET /news/research")
        articles = await newsroom.research.fetch_news()
        logger.info(f"Successfully fetched {len(articles)} research news articles")
        return NewsResponse(
            articles=articles,
            total_articles=len(articles),
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Error fetching research news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching research news: {str(e)}"
        )

@app.get("/news/all")
async def get_all_news():
    """Get all news categories in one request"""
    try:
        logger.info("API Call: GET /news/all")
        if newsroom.needs_update():
            news_data = await newsroom.update_all()
        else:
            news_data = newsroom.get_cached_news()
        logger.info("Successfully fetched all news categories")
        return news_data
    except Exception as e:
        logger.error(f"Error fetching all news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )

@app.get("/news/analyze")
async def analyze_news():
    """Get an analysis of current news trends and patterns"""
    try:
        logger.info("API Call: GET /news/analyze")
        news_data = await newsroom.update_all()
        if not news_data:
            return {
                "analysis": "Unable to generate analysis at this time. Please try again later.",
                "error": "Failed to fetch news data"
            }
        
        # Combine all articles for analysis
        all_articles = []
        for category in news_data.values():
            all_articles.extend(category)
            
        if not all_articles:
            return {
                "analysis": "No news articles available for analysis at this time.",
                "error": "No articles found"
            }
            
        logger.info(f"Analyzing {len(all_articles)} articles")
        analysis = await perplexity_agent.analyze_news_trends(all_articles)
        logger.info("Successfully generated news analysis")
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Error analyzing news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing news: {str(e)}"
        )

@app.get("/usage")
async def get_token_usage():
    """Get token usage statistics"""
    try:
        logger.info("API Call: GET /usage")
        usage = perplexity_agent.get_token_usage()
        logger.info(f"Successfully fetched token usage: {usage['total_tokens']} tokens, ${usage['total_cost']:.4f} cost")
        return usage
    except Exception as e:
        logger.error(f"Error fetching token usage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching token usage: {str(e)}"
        )

@app.get("/ai-trends")
async def get_ai_trends_summary():
    """Get AI trends summary for the past week"""
    try:
        logger.info("API Call: GET /ai-trends")
        summary = await perplexity_agent.generate_ai_trends_summary()
        logger.info("Successfully generated AI trends summary")
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error generating AI trends summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating AI trends summary: {str(e)}"
        )

if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 