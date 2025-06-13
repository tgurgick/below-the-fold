import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import time
import threading
from typing import Dict, List
import json
import logging
import io
import sys
from queue import Queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = "http://localhost:8000"
UPDATE_INTERVAL = 3600  # 1 hour in seconds
LOG_UPDATE_INTERVAL = 1  # seconds

# Custom theme configuration
def apply_custom_theme():
    st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #FAFAFA !important;
            }
            
            /* Cards and containers */
            .stContainer {
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 1rem;
                margin: 1rem 0;
            }
            
            /* Metrics */
            .stMetric {
                background-color: #1E1E1E;
                border-radius: 5px;
                padding: 1rem;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #1E1E1E;
                border-radius: 5px;
            }
            
            .stTabs [data-baseweb="tab"] {
                color: #FAFAFA;
            }
            
            /* Charts */
            .js-plotly-plot {
                background-color: #1E1E1E !important;
            }
            
            /* Text */
            p, .stMarkdown {
                color: #FAFAFA;
            }
            
            /* Dividers */
            hr {
                border-color: #2E2E2E;
            }
            
            /* Links */
            a {
                color: #00ACB5;
            }
            
            /* Captions */
            .stCaption {
                color: #A0A0A0;
            }
            
            /* Error messages */
            .stAlert {
                background-color: #2E2E2E;
            }
        </style>
    """, unsafe_allow_html=True)

def fetch_news() -> Dict:
    """Fetch news data from the API"""
    try:
        # Fetch both recent news and top stories
        recent_response = requests.get(f"{API_BASE_URL}/news/recent")
        recent_response.raise_for_status()
        recent_news = recent_response.json()

        top_response = requests.get(f"{API_BASE_URL}/news/top")
        top_response.raise_for_status()
        top_stories = top_response.json()

        return {
            "recent_news": recent_news,
            "top_stories": top_stories
        }
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to API server at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return None

def fetch_analysis() -> Dict:
    """Fetch news analysis from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/news/analyze")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to API server at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching analysis: {str(e)}")
        return None

def fetch_token_usage() -> Dict:
    """Fetch token usage statistics from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/usage")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to API server at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching token usage: {str(e)}")
        return None

def update_data():
    """Background task to update data periodically"""
    while True:
        st.session_state.news_data = fetch_news()
        st.session_state.analysis_data = fetch_analysis()
        st.session_state.token_usage = fetch_token_usage()
        st.session_state.last_update = datetime.now(timezone.utc)
        time.sleep(UPDATE_INTERVAL)

def initialize_session_state():
    """Initialize session state variables"""
    if 'news_data' not in st.session_state:
        st.session_state.news_data = fetch_news()
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = fetch_analysis()
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = fetch_token_usage()
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now(timezone.utc)

def display_token_usage(token_usage: Dict):
    """Display token usage statistics"""
    if not token_usage:
        return

    st.subheader("Token Usage & Cost")
    
    # Create metrics for token usage
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tokens", f"{token_usage['total_tokens']:,}")
    with col2:
        st.metric("Total Cost", f"${token_usage['total_cost']:.4f}")
    with col3:
        if token_usage['usage_history']:
            last_usage = token_usage['usage_history'][-1]
            st.metric("Last Request Tokens", f"{last_usage['total_tokens']:,}")

    # Create token usage history chart
    if token_usage['usage_history']:
        df = pd.DataFrame(token_usage['usage_history'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create line chart for token usage over time
        fig = px.line(
            df,
            x='timestamp',
            y='total_tokens',
            title="Token Usage Over Time",
            labels={'total_tokens': 'Tokens Used', 'timestamp': 'Time'},
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Create bar chart for cost distribution
        fig2 = px.bar(
            df,
            x='timestamp',
            y='cost',
            title="Cost per Request",
            labels={'cost': 'Cost ($)', 'timestamp': 'Time'},
            template="plotly_dark"
        )
        st.plotly_chart(fig2, use_container_width=True)

def display_news_articles(news_data: Dict):
    """Display news articles in a grid layout"""
    if not news_data:
        return

    # Create tabs for recent news and top stories
    recent_tab, top_tab = st.tabs(["Recent News (Last 24 Hours)", "Top Stories (Last 7 Days)"])

    with recent_tab:
        if news_data.get("recent_news"):
            articles = news_data["recent_news"].get("articles", [])
            if articles:
                for article in articles:
                    with st.container():
                        st.subheader(article["title"])
                        st.write(article["summary"])
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.caption(f"Source: {article['source']}")
                            st.caption(f"Published: {article['published_at']}")
                        with col2:
                            st.caption(f"Category: {article['category']}")
                            st.caption(f"Importance: {article['importance_score']:.2f}")
                        st.markdown(f"[Read more]({article['url']})")
                        st.divider()
            else:
                st.info("No recent news articles available.")
        else:
            st.info("No recent news data available.")

    with top_tab:
        if news_data.get("top_stories"):
            articles = news_data["top_stories"].get("articles", [])
            if articles:
                for article in articles:
                    with st.container():
                        st.subheader(article["title"])
                        st.write(article["summary"])
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.caption(f"Source: {article['source']}")
                            st.caption(f"Published: {article['published_at']}")
                        with col2:
                            st.caption(f"Category: {article['category']}")
                            st.caption(f"Importance: {article['importance_score']:.2f}")
                        st.markdown(f"[Read more]({article['url']})")
                        st.divider()
            else:
                st.info("No top stories available.")
        else:
            st.info("No top stories data available.")

def display_analysis(analysis_data: Dict):
    """Display news analysis"""
    if not analysis_data or 'analysis' not in analysis_data:
        st.warning("No analysis data available")
        return

    st.subheader("Tech & AI News Analysis")
    st.write(analysis_data['analysis'])

def display_metrics(news_data: Dict):
    """Display key metrics"""
    if not news_data or 'articles' not in news_data:
        return

    articles = news_data['articles']
    df = pd.DataFrame(articles)
    
    # Calculate metrics
    avg_importance = df['importance_score'].mean()
    avg_sentiment = df['sentiment_score'].mean()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", len(articles))
    with col2:
        st.metric("Avg. Importance", f"{avg_importance:.2f}")
    with col3:
        st.metric("Avg. Sentiment", f"{avg_sentiment:.2f}")
    with col4:
        ai_articles = df[df['category'].str.contains('AI|ML', case=False, na=False)]
        st.metric("AI/ML Articles", len(ai_articles))

def display_category_distribution(news_data: Dict):
    """Display category distribution chart"""
    if not news_data or 'articles' not in news_data:
        return

    df = pd.DataFrame(news_data['articles'])
    
    # Create category distribution
    category_counts = df['category'].value_counts()
    
    # Create pie chart
    fig = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="News Category Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_trend(news_data: Dict):
    """Display sentiment trend by category"""
    if not news_data or 'articles' not in news_data:
        return

    df = pd.DataFrame(news_data['articles'])
    
    # Calculate average sentiment by category
    sentiment_by_category = df.groupby('category')['sentiment_score'].mean().reset_index()
    
    # Create bar chart
    fig = px.bar(
        sentiment_by_category,
        x='category',
        y='sentiment_score',
        title="Average Sentiment by Category",
        color='sentiment_score',
        color_continuous_scale=['red', 'gray', 'green'],
        labels={'sentiment_score': 'Sentiment Score', 'category': 'Category'},
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_startup_summary(news_data: Dict):
    """Display a condensed summary of recent tech news trends"""
    if not news_data or 'articles' not in news_data:
        return

    articles = news_data['articles']
    df = pd.DataFrame(articles)
    
    # Convert published_at strings to datetime objects using ISO8601 format
    df['published_at'] = pd.to_datetime(df['published_at'], format='ISO8601')
    
    # Filter for articles from the last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_articles = df[df['published_at'] >= seven_days_ago]
    
    if len(recent_articles) == 0:
        return
    
    st.subheader("📊 Tech News Digest")
    
    # Create three columns for different news categories
    col1, col2, col3 = st.columns(3)
    
    # Define more specific masks for each category
    funding_mask = recent_articles['title'].str.contains(
        'funding|raise|valuation|series|seed|round|venture|investment|acquired|acquisition|merger|M&A|bought|purchased', 
        case=False, na=False
    )
    
    research_mask = recent_articles['title'].str.contains(
        'research|breakthrough|model|algorithm|study|paper|SOTA|neural|GPT|LLM|machine learning|AI model|new technology|innovation|technical', 
        case=False, na=False
    )
    
    # Get articles for each category
    funding_news = recent_articles[funding_mask].head(3)
    research_news = recent_articles[research_mask].head(3)
    
    # Get remaining articles for major news, excluding those already in funding or research
    major_news = recent_articles[~(funding_mask | research_mask)].nlargest(3, 'importance_score')
    
    with col1:
        st.markdown("**🔬 Major News**")
        for _, story in major_news.iterrows():
            st.markdown(f"{story['title']}")
            if 'summary' in story and pd.notna(story['summary']):
                st.caption(f"_{story['summary'][:100]}..._")
    
    with col2:
        st.markdown("**💰 Funding & M&A**")
        if len(funding_news) == 0:
            st.caption("_No recent funding or M&A news_")
        for _, story in funding_news.iterrows():
            st.markdown(f"{story['title']}")
            if 'summary' in story and pd.notna(story['summary']):
                st.caption(f"_{story['summary'][:100]}..._")
    
    with col3:
        st.markdown("**🤖 SOTA & Research**")
        if len(research_news) == 0:
            st.caption("_No recent research breakthroughs_")
        for _, story in research_news.iterrows():
            st.markdown(f"{story['title']}")
            if 'summary' in story and pd.notna(story['summary']):
                st.caption(f"_{story['summary'][:100]}..._")
    
    st.markdown("---")

class LogHandler(logging.Handler):
    def __init__(self, max_logs=1000):
        super().__init__()
        self.log_buffer = []
        self.max_logs = max_logs
        self.log_queue = Queue()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
            self.log_buffer.append(msg)
            if len(self.log_buffer) > self.max_logs:
                self.log_buffer.pop(0)
        except Exception:
            self.handleError(record)

# Initialize the log handler
log_handler = LogHandler()
logging.getLogger().addHandler(log_handler)

def fetch_logs() -> List[str]:
    """Fetch new logs from the queue"""
    logs = []
    while not log_handler.log_queue.empty():
        logs.append(log_handler.log_queue.get())
    return logs

def display_logs():
    """Display logs in a streaming format"""
    st.subheader("Application Logs")
    
    # Create a container for logs
    log_container = st.empty()
    
    # Initialize session state for logs if not exists
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    # Function to update logs
    def update_logs():
        while True:
            new_logs = fetch_logs()
            if new_logs:
                st.session_state.logs.extend(new_logs)
                # Keep only the last 1000 logs
                if len(st.session_state.logs) > 1000:
                    st.session_state.logs = st.session_state.logs[-1000:]
                # Update the display
                log_container.code("\n".join(st.session_state.logs), language="text")
            time.sleep(LOG_UPDATE_INTERVAL)
    
    # Start the log update thread if not already running
    if 'log_thread' not in st.session_state:
        st.session_state.log_thread = threading.Thread(target=update_logs, daemon=True)
        st.session_state.log_thread.start()
    
    # Display current logs
    log_container.code("\n".join(st.session_state.logs), language="text")
    
    # Add a clear logs button
    if st.button("Clear Logs"):
        st.session_state.logs = []
        log_container.code("", language="text")

def main():
    st.set_page_config(
        page_title="Below the Fold - Tech News Dashboard",
        page_icon="📰",
        layout="wide"
    )

    # Apply custom theme
    apply_custom_theme()

    # Initialize session state
    initialize_session_state()

    st.title("Below the Fold - Tech News Dashboard")
    
    # Display startup summary
    display_startup_summary(st.session_state.news_data)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["News Feed", "Token Usage", "Logs"])
    
    with tab1:
        display_news_articles(st.session_state.news_data)
    
    with tab2:
        display_token_usage(st.session_state.token_usage)
    
    with tab3:
        display_logs()

if __name__ == "__main__":
    try:
        logger.info("Starting dashboard application")
        main()
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}") 