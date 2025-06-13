import os
import json
from datetime import datetime, timezone
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from ..models.news import NewsArticle, NewsResponse
from ..config.loader import ConfigLoader
from ..utils.token_calculator import TokenCalculator

load_dotenv()

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

    async def get_top_news(self, num_articles: int = 10) -> NewsResponse:
        """
        Fetch and process top news stories using Perplexity's API.
        
        Args:
            num_articles (int): Number of articles to fetch
            
        Returns:
            NewsResponse: Processed news articles
        """
        prompt = self.config_loader.get_prompt('prompts.yaml', 'news_fetch').format(
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
                            "content": "You are a helpful assistant that provides news in a structured JSON format. Always respond with valid JSON. Each article must include: headline, summary, source, url, publication_time (in ISO format with timezone), category, importance_score (0-1), sentiment_score (-1 to 1), and why_it_matters (a brief explanation of why this story is significant)."
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
            content = response.json()["choices"][0]["message"]["content"]
            
            # Track token usage
            self.token_calculator.add_usage(prompt, content)
            
            try:
                news_data = json.loads(content)
            except json.JSONDecodeError:
                # If the response isn't valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    news_data = json.loads(json_match.group())
                else:
                    raise Exception("Could not parse news data from API response")
            
            articles = []
            for article in news_data:
                # Provide default values for missing fields
                published_at = article.get("publication_time")
                if published_at:
                    try:
                        published_at = datetime.fromisoformat(published_at)
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except ValueError:
                        published_at = datetime.now(timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)

                articles.append(NewsArticle(
                    title=article.get("headline", "No Title"),
                    summary=article.get("summary", "No Summary"),
                    source=article.get("source", "Unknown Source"),
                    url=article.get("url", ""),
                    published_at=published_at,
                    category=article.get("category", "General"),
                    importance_score=float(article.get("importance_score", 0.5)),
                    sentiment_score=float(article.get("sentiment_score", 0.0)),
                    why_it_matters=article.get("why_it_matters", "Analysis not available")
                ))
            
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