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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a custom stream handler to capture logs
class StreamlitLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_buffer = []
        self.max_logs = 1000  # Keep last 1000 log entries

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_buffer.append(msg)
            if len(self.log_buffer) > self.max_logs:
                self.log_buffer.pop(0)
        except Exception:
            self.handleError(record)

# Add the custom handler to the root logger
log_handler = StreamlitLogHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_handler)

# Constants
API_BASE_URL = "http://localhost:8000"
UPDATE_INTERVAL = 3600  # 1 hour in seconds

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
    """Fetch news from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/news/top")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
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
    """Display news articles in a grid"""
    if not news_data or 'articles' not in news_data:
        st.warning("No news data available")
        return

    articles = news_data['articles']
    
    # Create a DataFrame for better visualization
    df = pd.DataFrame(articles)
    
    # Sort by published_at in descending order (newest first)
    df = df.sort_values('published_at', ascending=False)
    
    # Display each article in a card-like format
    for _, article in df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(article['title'])
                st.write(article['summary'])
                st.caption(f"Source: {article['source']} | Published: {article['published_at']}")
                st.caption(f"Category: {article['category']}")
                # Add why it matters section
                st.markdown("**Why it matters:**")
                st.write(article.get('why_it_matters', 'Analysis not available'))
            with col2:
                # Display importance and sentiment scores with appropriate delta colors
                st.metric(
                    "Importance",
                    f"{article['importance_score']:.2f}",
                    delta=None,
                    delta_color="normal"
                )
                st.metric(
                    "Sentiment",
                    f"{article['sentiment_score']:.2f}",
                    delta=None,
                    delta_color="normal"
                )
            st.markdown("---")

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
    """Display a summary of recent news trends on startup"""
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
    
    st.subheader("📊 Recent News Summary")
    
    # Group by category and count articles
    category_counts = recent_articles['category'].value_counts()
    
    # Display top categories
    st.write("**Top Categories in the Last 7 Days:**")
    for category, count in category_counts.head(3).items():
        st.write(f"- {category}: {count} articles")
    
    # Calculate average sentiment by category
    sentiment_by_category = recent_articles.groupby('category')['sentiment_score'].mean()
    
    # Display sentiment trends
    st.write("\n**Sentiment Trends:**")
    for category, sentiment in sentiment_by_category.items():
        sentiment_label = "Positive" if sentiment > 0.2 else "Negative" if sentiment < -0.2 else "Neutral"
        st.write(f"- {category}: {sentiment_label} ({sentiment:.2f})")
    
    # Display most important stories
    st.write("\n**Most Important Stories:**")
    important_stories = recent_articles.nlargest(3, 'importance_score')
    for _, story in important_stories.iterrows():
        st.write(f"- {story['title']} (Importance: {story['importance_score']:.2f})")
    
    st.markdown("---")

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
        st.subheader("Application Logs")
        # Display logs in a monospace font with a dark background
        log_text = "\n".join(log_handler.log_buffer)
        st.code(log_text, language="text")
        
        # Add a refresh button
        if st.button("Refresh Logs"):
            st.rerun()

if __name__ == "__main__":
    try:
        logger.info("Starting dashboard application")
        main()
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}") 