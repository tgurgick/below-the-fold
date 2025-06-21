import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

import json
from datetime import datetime, timezone
import requests
from typing import List, Dict, Any, Optional
from src.models.news import NewsArticle, NewsResponse
from src.config.loader import ConfigLoader
from src.utils.token_calculator import TokenCalculator
import logging

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

    async def get_top_news(self, num_articles: int = 10, prompt_key: str = 'news_fetch', categories: List[str] = None) -> NewsResponse:
        """
        Fetch and process top news stories using Perplexity's API.
        
        Args:
            num_articles (int): Number of articles to fetch
            prompt_key (str): Key of the prompt template to use (default: 'news_fetch')
            categories (List[str], optional): List of categories to filter news by
            
        Returns:
            NewsResponse: Processed news articles
        """
        logger.info(f"PerplexityAgent: Starting news fetch - prompt_key={prompt_key}, num_articles={num_articles}, categories={categories}")
        
        prompt = self.config_loader.get_prompt('prompts.yaml', prompt_key).format(
            num_articles=num_articles,
            categories=', '.join(categories) if categories else 'all'
        )
        
        logger.debug(f"PerplexityAgent: Generated prompt for {prompt_key} with {len(prompt)} characters")

        try:
            logger.info(f"PerplexityAgent: Making API call to Perplexity with model=sonar")
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
            
            logger.info(f"PerplexityAgent: API call successful - status_code={response.status_code}")
            
            # Parse the response and convert to NewsArticle objects
            response_json = response.json()
            if "choices" not in response_json or not response_json["choices"]:
                logger.error("PerplexityAgent: Invalid response format from Perplexity API")
                raise Exception("Invalid response format from Perplexity API")
                
            content = response_json["choices"][0]["message"]["content"]
            logger.debug(f"PerplexityAgent: Raw API response content length: {len(content)} characters")
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content, "sonar")
            logger.info(f"PerplexityAgent: Token usage tracked for {prompt_key}")
            
            try:
                # First try to parse the content directly
                news_data = json.loads(content)
                logger.info(f"PerplexityAgent: Successfully parsed JSON directly - found {len(news_data)} articles")
            except json.JSONDecodeError as e:
                logger.warning(f"PerplexityAgent: Failed to parse JSON directly: {str(e)}")
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        news_data = json.loads(json_match.group())
                        logger.info(f"PerplexityAgent: Successfully parsed JSON from extracted content - found {len(news_data)} articles")
                    except json.JSONDecodeError as e:
                        logger.error(f"PerplexityAgent: Failed to parse JSON from extracted content: {str(e)}")
                        raise Exception("Could not parse JSON from extracted content")
                else:
                    logger.error("PerplexityAgent: Could not find JSON array in API response")
                    raise Exception("Could not find JSON array in API response")
            
            if not isinstance(news_data, list):
                logger.error(f"PerplexityAgent: Expected a JSON array of articles, got: {type(news_data)}")
                raise Exception("Expected a JSON array of articles")
            
            articles = []
            seen_sources = set()
            
            logger.info(f"PerplexityAgent: Processing {len(news_data)} raw articles")
            
            for i, article in enumerate(news_data):
                if not isinstance(article, dict):
                    logger.warning(f"PerplexityAgent: Skipping article {i}: not a dictionary")
                    continue
                    
                # Skip articles with missing required fields
                missing_fields = [k for k in ['headline', 'summary', 'source', 'url'] if k not in article]
                if missing_fields:
                    logger.warning(f"PerplexityAgent: Skipping article {i}: missing required fields: {missing_fields}")
                    continue
                    
                # Skip if we've already seen this source
                source = article.get('source', '').lower()
                if source in seen_sources:
                    logger.warning(f"PerplexityAgent: Skipping article {i}: duplicate source: {source}")
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
                        logger.warning(f"PerplexityAgent: Invalid publication time for article {i}: {published_at}, using current time")
                        published_at = datetime.now(timezone.utc)
                else:
                    logger.warning(f"PerplexityAgent: No publication time for article {i}, using current time")
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
                    logger.debug(f"PerplexityAgent: Successfully added article {i}: {news_article.title}")
                except ValueError as e:
                    logger.warning(f"PerplexityAgent: Skipping article {i} due to validation error: {str(e)}")
                    continue
            
            logger.info(f"PerplexityAgent: Successfully processed {len(articles)} valid articles from {len(news_data)} raw articles")
            
            if not articles:
                logger.error("PerplexityAgent: No valid articles found in API response after processing")
                raise Exception("No valid articles found in API response")
            
            logger.info(f"PerplexityAgent: News fetch completed successfully - returning {len(articles)} articles")
            return NewsResponse(
                articles=articles,
                total_articles=len(articles),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"PerplexityAgent: Error fetching news from Perplexity API: {str(e)}", exc_info=True)
            raise Exception(f"Error fetching news from Perplexity API: {str(e)}")

    async def analyze_news_trends(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analyze trends and patterns in the news articles.
        
        Args:
            articles (List[NewsArticle]): List of news articles to analyze
            
        Returns:
            Dict[str, Any]: Analysis results including trends and patterns
        """
        logger.info(f"PerplexityAgent: Starting news trends analysis for {len(articles)} articles")
        
        # Convert articles to a format suitable for analysis
        articles_text = "\n".join([
            f"Title: {article.title}\nSummary: {article.summary}\nCategory: {article.category}"
            for article in articles
        ])
        
        logger.debug(f"PerplexityAgent: Generated articles text for analysis with {len(articles_text)} characters")
        
        prompt = self.config_loader.get_prompt('prompts.yaml', 'news_analysis').format(
            articles_text=articles_text
        )

        try:
            logger.info(f"PerplexityAgent: Making API call for news analysis with model=sonar")
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
            
            logger.info(f"PerplexityAgent: News analysis API call successful - status_code={response.status_code}")
            
            content = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"PerplexityAgent: News analysis response length: {len(content)} characters")
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content, "sonar")
            logger.info(f"PerplexityAgent: Token usage tracked for news analysis")
            
            logger.info(f"PerplexityAgent: News trends analysis completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"PerplexityAgent: Error analyzing news trends: {str(e)}", exc_info=True)
            raise Exception(f"Error analyzing news trends: {str(e)}")

    async def generate_ai_trends_summary(self) -> str:
        """
        Generate a summary of AI trends over the past week.
        
        Returns:
            str: AI trends summary
        """
        logger.info(f"PerplexityAgent: Starting AI trends summary generation")
        
        prompt = self.config_loader.get_prompt('prompts.yaml', 'ai_trends_summary')
        logger.debug(f"PerplexityAgent: Generated AI trends prompt with {len(prompt)} characters")

        try:
            logger.info(f"PerplexityAgent: Making API call for AI trends summary with model=sonar")
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
                            "content": "You are an AI trends analyst. Provide insightful, well-structured summaries of AI developments."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            logger.info(f"PerplexityAgent: AI trends summary API call successful - status_code={response.status_code}")
            
            content = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"PerplexityAgent: AI trends summary response length: {len(content)} characters")
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content, "sonar")
            logger.info(f"PerplexityAgent: Token usage tracked for AI trends summary")
            
            logger.info(f"PerplexityAgent: AI trends summary generation completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"PerplexityAgent: Error generating AI trends summary: {str(e)}", exc_info=True)
            raise Exception(f"Error generating AI trends summary: {str(e)}")

    async def generate_executive_action_items(self) -> str:
        """
        Generate executive action items with citations.
        
        Returns:
            str: Executive action items with citations
        """
        logger.info(f"PerplexityAgent: Starting executive action items generation")
        
        prompt = self.config_loader.get_prompt('prompts.yaml', 'executive_action_items')
        logger.debug(f"PerplexityAgent: Generated executive action items prompt with {len(prompt)} characters")

        try:
            logger.info(f"PerplexityAgent: Making API call for executive action items with model=sonar")
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
                            "content": "You are an executive strategy consultant. Provide specific, actionable strategic items for AI leaders with proper citations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            logger.info(f"PerplexityAgent: Executive action items API call successful - status_code={response.status_code}")
            
            content = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"PerplexityAgent: Executive action items response length: {len(content)} characters")
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content, "sonar")
            logger.info(f"PerplexityAgent: Token usage tracked for executive action items")
            
            logger.info(f"PerplexityAgent: Executive action items generation completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"PerplexityAgent: Error generating executive action items: {str(e)}", exc_info=True)
            raise Exception(f"Error generating executive action items: {str(e)}")

    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get the current token usage statistics.
        
        Returns:
            Dict[str, Any]: Token usage statistics
        """
        return self.token_calculator.get_usage_summary() 