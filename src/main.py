from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .agents.perplexity_agent import PerplexityAgent
from .models.news import NewsResponse
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
perplexity_agent = PerplexityAgent()

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Below the Fold API"}

@app.get("/news/top", response_model=NewsResponse)
async def get_top_news(num_articles: int = 10):
    """
    Get the top news stories for today.
    
    Args:
        num_articles (int): Number of articles to fetch (default: 10)
        
    Returns:
        NewsResponse: Top news stories with analysis
    """
    try:
        logger.info("Fetching top news articles")
        news_response = await perplexity_agent.get_top_news(num_articles)
        logger.info(f"Successfully fetched {len(news_response.articles)} articles")
        return news_response
    except Exception as e:
        logger.error(f"Error fetching top news: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/analyze")
async def analyze_news():
    """
    Get an analysis of current news trends and patterns.
    
    Returns:
        dict: Analysis of news trends and patterns
    """
    try:
        # First get the top news
        logger.info("Fetching top news for analysis")
        news_response = await perplexity_agent.get_top_news()
        logger.info(f"Successfully fetched {len(news_response.articles)} articles for analysis")
        # Then analyze the trends
        analysis = await perplexity_agent.analyze_news_trends(news_response.articles)
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Error analyzing news: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage")
async def get_token_usage():
    """
    Get token usage statistics.
    
    Returns:
        dict: Token usage statistics including total tokens, cost, and history
    """
    try:
        logger.info("Fetching token usage statistics")
        usage = perplexity_agent.get_token_usage()
        logger.info("Successfully fetched token usage")
        return usage
    except Exception as e:
        logger.error(f"Error fetching token usage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 