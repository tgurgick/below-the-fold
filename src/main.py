from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .agents.perplexity_agent import PerplexityAgent
from .models.news import NewsResponse
import uvicorn
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('LOG_LEVEL') == 'DEBUG' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize the Perplexity agent
try:
    perplexity_agent = PerplexityAgent()
    logger.info("Successfully initialized PerplexityAgent")
except ValueError as e:
    logger.error(f"Failed to initialize PerplexityAgent: {str(e)}")
    raise Exception("Failed to initialize news agent. Please check your environment variables.")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Below the Fold API"}

@app.get("/news/recent", response_model=NewsResponse)
async def get_recent_news(num_articles: int = 10):
    """
    Get the most recent technology and AI news stories from the last 24 hours.
    
    Args:
        num_articles (int): Number of articles to fetch (default: 10)
        
    Returns:
        NewsResponse: Recent news stories
    """
    try:
        logger.info(f"API Call: GET /news/recent?num_articles={num_articles}")
        news_response = await perplexity_agent.get_top_news(num_articles, prompt_key='news_fetch')
        logger.info(f"Successfully fetched {len(news_response.articles)} recent articles")
        logger.debug(f"Recent articles: {[article.title for article in news_response.articles]}")
        return news_response
    except ValueError as e:
        logger.error(f"Validation error in news data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid news data: {str(e)}. Please ensure all sources are reputable news outlets."
        )
    except Exception as e:
        logger.error(f"Error fetching recent news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )

@app.get("/news/top", response_model=NewsResponse)
async def get_top_stories(num_articles: int = 10):
    """
    Get the most significant technology and AI news stories from the last 7 days.
    
    Args:
        num_articles (int): Number of articles to fetch (default: 10)
        
    Returns:
        NewsResponse: Top news stories
    """
    try:
        logger.info(f"API Call: GET /news/top?num_articles={num_articles}")
        news_response = await perplexity_agent.get_top_news(num_articles, prompt_key='top_stories')
        logger.info(f"Successfully fetched {len(news_response.articles)} top stories")
        logger.debug(f"Top stories: {[article.title for article in news_response.articles]}")
        return news_response
    except ValueError as e:
        logger.error(f"Validation error in news data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid news data: {str(e)}. Please ensure all sources are reputable news outlets."
        )
    except Exception as e:
        logger.error(f"Error fetching top stories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )

@app.get("/news/analyze")
async def analyze_news():
    """
    Get an analysis of current news trends and patterns.
    
    Returns:
        dict: Analysis of news trends and patterns
    """
    try:
        logger.info("API Call: GET /news/analyze")
        # First get both recent news and top stories
        logger.info("Fetching news for analysis")
        recent_news = await perplexity_agent.get_top_news(prompt_key='news_fetch')
        top_stories = await perplexity_agent.get_top_news(prompt_key='top_stories')
        
        # Combine articles for analysis
        all_articles = recent_news.articles + top_stories.articles
        logger.info(f"Combined {len(all_articles)} articles for analysis")
        
        # Then analyze the trends
        analysis = await perplexity_agent.analyze_news_trends(all_articles)
        logger.info("Successfully generated news analysis")
        logger.debug(f"Analysis summary: {analysis[:200]}...")  # Log first 200 chars of analysis
        return {"analysis": analysis}
    except ValueError as e:
        logger.error(f"Validation error in news data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid news data: {str(e)}. Please ensure all sources are reputable news outlets."
        )
    except Exception as e:
        logger.error(f"Error analyzing news: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing news: {str(e)}"
        )

@app.get("/usage")
async def get_token_usage():
    """
    Get token usage statistics.
    
    Returns:
        dict: Token usage statistics including total tokens, cost, and history
    """
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

if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 