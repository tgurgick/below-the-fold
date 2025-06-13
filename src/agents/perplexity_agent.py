import os
import json
from datetime import datetime, timezone
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from ..models.news import NewsArticle, NewsResponse
from ..config.loader import ConfigLoader
from ..utils.token_calculator import TokenCalculator
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class PerplexityAgent:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.config_loader = ConfigLoader()
        self.token_calculator = TokenCalculator()

    async def get_top_news(self, num_articles: int = 10, prompt_key: str = 'news_fetch') -> NewsResponse:
        """
        Fetch and process top news stories using Perplexity's API.
        
        Args:
            num_articles (int): Number of articles to fetch
            prompt_key (str): Key of the prompt template to use (default: 'news_fetch')
            
        Returns:
            NewsResponse: Processed news articles
        """
        prompt = self.config_loader.get_prompt('prompts.yaml', prompt_key).format(
            num_articles=num_articles
        )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a news aggregation assistant that provides technology and AI news in a structured JSON format. 
Your response must be a valid JSON array of articles. Each article must be a JSON object with these exact fields:
{
    "headline": "string",
    "summary": "string",
    "source": "string (must be a real, reputable news outlet like The Verge, TechCrunch, Wired, MIT Technology Review, The New York Times, Financial Times, Nature, Science, etc.)",
    "url": "string (must be a valid URL from the source)",
    "publication_time": "string (in ISO format with timezone)",
    "category": "string",
    "importance_score": number (0-1),
    "sentiment_score": number (-1 to 1),
    "why_it_matters": "string"
}

Requirements:
- Each article must come from a different reputable source
- Sources must be real, established news outlets or academic institutions
- URLs must be valid and point to actual articles
- Never use generic or made-up sources
- If you cannot find a reputable source for a story, skip it and select another"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            # Parse the response and convert to NewsArticle objects
            response_json = response.json()
            if "choices" not in response_json or not response_json["choices"]:
                raise Exception("Invalid response format from Perplexity API")
                
            content = response_json["choices"][0]["message"]["content"]
            logger.debug(f"Raw API response content: {content}")
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content)
            
            try:
                # First try to parse the content directly
                news_data = json.loads(content)
                logger.debug(f"Successfully parsed JSON directly: {news_data}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON directly: {str(e)}")
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        news_data = json.loads(json_match.group())
                        logger.debug(f"Successfully parsed JSON from extracted content: {news_data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from extracted content: {str(e)}")
                        raise Exception("Could not parse JSON from extracted content")
                else:
                    logger.error("Could not find JSON array in API response")
                    raise Exception("Could not find JSON array in API response")
            
            if not isinstance(news_data, list):
                logger.error(f"Expected a JSON array of articles, got: {type(news_data)}")
                raise Exception("Expected a JSON array of articles")
            
            articles = []
            seen_sources = set()  # Track sources to ensure uniqueness
            
            for i, article in enumerate(news_data):
                if not isinstance(article, dict):
                    logger.warning(f"Skipping article {i}: not a dictionary")
                    continue
                    
                # Skip articles with missing required fields
                missing_fields = [k for k in ['headline', 'summary', 'source', 'url'] if k not in article]
                if missing_fields:
                    logger.warning(f"Skipping article {i}: missing required fields: {missing_fields}")
                    continue
                    
                # Skip if we've already seen this source
                source = article.get('source', '').lower()
                if source in seen_sources:
                    logger.warning(f"Skipping article {i}: duplicate source: {source}")
                    continue
                seen_sources.add(source)
                
                # Handle publication time
                published_at = article.get("publication_time")
                if published_at:
                    try:
                        published_at = datetime.fromisoformat(published_at)
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        logger.warning(f"Invalid publication time for article {i}: {published_at}, using current time")
                        published_at = datetime.now(timezone.utc)
                else:
                    logger.warning(f"No publication time for article {i}, using current time")
                    published_at = datetime.now(timezone.utc)

                try:
                    news_article = NewsArticle(
                        title=article.get("headline", "No Title"),
                        summary=article.get("summary", "No Summary"),
                        source=article.get("source", ""),
                        url=article.get("url", ""),
                        published_at=published_at,
                        category=article.get("category", "General"),
                        importance_score=float(article.get("importance_score", 0.5)),
                        sentiment_score=float(article.get("sentiment_score", 0.0)),
                        why_it_matters=article.get("why_it_matters", "Analysis not available")
                    )
                    articles.append(news_article)
                    logger.debug(f"Successfully added article {i}: {news_article.title}")
                except ValueError as e:
                    logger.warning(f"Skipping article {i} due to validation error: {str(e)}")
                    continue
            
            if not articles:
                logger.error("No valid articles found in API response after processing")
                raise Exception("No valid articles found in API response")
            
            logger.info(f"Successfully processed {len(articles)} articles")
            return NewsResponse(
                articles=articles,
                total_articles=len(articles),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            raise Exception(f"Error fetching news from Perplexity API: {str(e)}")

    async def analyze_news_trends(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analyze trends and patterns in the news articles.
        
        Args:
            articles (List[NewsArticle]): List of news articles to analyze
            
        Returns:
            Dict[str, Any]: Analysis results including trends and patterns
        """
        # Convert articles to a format suitable for analysis
        articles_text = "\n".join([
            f"Title: {article.title}\nSummary: {article.summary}\nCategory: {article.category}"
            for article in articles
        ])
        
        prompt = self.config_loader.get_prompt('prompts.yaml', 'news_analysis').format(
            articles_text=articles_text
        )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be precise and concise."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content)
            
            return content
            
        except Exception as e:
            raise Exception(f"Error analyzing news trends: {str(e)}")

    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get the current token usage statistics.
        
        Returns:
            Dict[str, Any]: Token usage statistics
        """
        return self.token_calculator.get_usage_summary() 