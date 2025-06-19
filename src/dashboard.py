import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import time
import threading
from typing import Dict, List, Optional
import json
import logging
import io
import sys
from queue import Queue
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('LOG_LEVEL') == 'DEBUG' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a test log message
logger.info("Dashboard application starting up")

# Constants
API_BASE_URL = "http://localhost:8000"
DEFAULT_UPDATE_INTERVAL = 3600  # 1 hour in seconds
LOG_UPDATE_INTERVAL = 1  # seconds

# Update interval options (in seconds)
UPDATE_INTERVALS = {
    "15 minutes": 900,
    "30 minutes": 1800,
    "1 hour": 3600
}

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
            
            /* Reduce font sizes for better space usage */
            .stMarkdown {
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            /* Smaller text for better density */
            p, .stMarkdown p {
                font-size: 0.85rem;
                line-height: 1.3;
            }
            
            /* Smaller headers */
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.5rem !important; }
            h3 { font-size: 1.2rem !important; }
            h4 { font-size: 1.1rem !important; }
            
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

def fetch_news(category: str) -> List[Dict]:
    """Fetch news articles for a specific category"""
    try:
        logger.info(f"Fetching {category} news")
        response = requests.get(f"{API_BASE_URL}/news/{category}")
        response.raise_for_status()
        data = response.json()
        articles = data.get('articles', [])
        logger.info(f"Successfully fetched {len(articles)} {category} articles")
        return articles
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the API server")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching {category} news: {str(e)}")
        return []

def fetch_analysis() -> Optional[str]:
    """Fetch news analysis"""
    try:
        logger.info("Fetching news analysis")
        response = requests.get(f"{API_BASE_URL}/news/analyze")
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            logger.error(f"API returned error: {data['error']}")
            return None
        analysis = data.get('analysis')
        if not analysis:
            logger.warning("No analysis data received")
            return None
        logger.info("Successfully fetched news analysis")
        return analysis
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the API server")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching analysis: {str(e)}")
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

def fetch_ai_trends() -> Optional[str]:
    """Fetch AI trends summary from the API"""
    try:
        logger.info("Fetching AI trends summary")
        response = requests.get(f"{API_BASE_URL}/ai-trends")
        response.raise_for_status()
        data = response.json()
        summary = data.get('summary')
        if not summary:
            logger.warning("No AI trends summary received")
            return None
        logger.info("Successfully fetched AI trends summary")
        return summary
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the API server")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching AI trends: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now(timezone.utc)
    if 'next_update' not in st.session_state:
        st.session_state.next_update = datetime.now(timezone.utc) + timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
    if 'update_interval' not in st.session_state:
        st.session_state.update_interval = DEFAULT_UPDATE_INTERVAL
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'news_data' not in st.session_state:
        st.session_state.news_data = {}
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = fetch_token_usage()
    if 'last_log_update' not in st.session_state:
        st.session_state.last_log_update = datetime.now(timezone.utc)

def check_for_updates():
    """Check if it's time to update the data"""
    current_time = datetime.now(timezone.utc)
    
    # Ensure next_update is set
    if not st.session_state.next_update:
        st.session_state.next_update = current_time + timedelta(seconds=st.session_state.update_interval)
        return False
        
    if current_time >= st.session_state.next_update:
        logger.info("Scheduled update triggered")
        news_data = {}
        for category in ['breaking', 'top', 'funding', 'research']:
            articles = fetch_news(category)
            if articles:
                news_data[category] = articles
        
        if news_data:
            st.session_state.news_data = news_data
            st.session_state.last_update = current_time
            st.session_state.next_update = current_time + timedelta(seconds=st.session_state.update_interval)
            
            # Also refresh token usage periodically
            refresh_token_usage()
            
            return True
    return False

def display_token_usage(token_usage: Dict):
    """Display token usage statistics"""
    st.subheader("💰 Token Usage & Cost")
    
    # Add refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", key="refresh_tokens", help="Update token usage data"):
            if refresh_token_usage():
                st.success("Token usage updated!")
            else:
                st.error("Failed to update token usage")
            st.rerun()
    with col2:
        st.caption("Last updated: " + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    
    if not token_usage:
        st.warning("No token usage data available. Make sure the API server is running and try refreshing.")
        return

    # Create metrics for token usage
    col1, col2, col3 = st.columns(3)
    with col1:
        total_tokens = token_usage.get('total_tokens', 0)
        st.metric("Total Tokens", f"{total_tokens:,}")
    with col2:
        total_cost = token_usage.get('total_cost', 0.0)
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col3:
        usage_history = token_usage.get('usage_history', [])
        if usage_history:
            last_usage = usage_history[-1]
            last_tokens = last_usage.get('total_tokens', 0)
            st.metric("Last Request Tokens", f"{last_tokens:,}")
        else:
            st.metric("Last Request Tokens", "0")

    # Create token usage history chart
    if usage_history:
        try:
            df = pd.DataFrame(usage_history)
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
            
            # Show usage history table
            st.subheader("Recent Usage History")
            display_df = df.copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df['cost'] = display_df['cost'].apply(lambda x: f"${x:.4f}")
            st.dataframe(display_df[['timestamp', 'total_tokens', 'cost', 'model']], use_container_width=True)
            
        except Exception as e:
            st.error(f"Error displaying token usage charts: {str(e)}")
    else:
        st.info("No usage history available yet. Token usage will appear here after making API requests.")

def display_news_articles(articles: List[Dict], category: str):
    """Display news articles for a specific category"""
    if not articles:
        st.warning(f"No {category} articles available at this time.")
        return
        
    st.subheader(f" {category}")
    
    # Create a more organized layout for articles
    for i, article in enumerate(articles):
        with st.container():
            # Create a card-like appearance
            st.markdown("---")
            
            # Article header with title and link
            title = article.get('title', 'No Title')
            url = article.get('url', '#')
            if url and url != '#':
                st.markdown(f"### [{title}]({url})")
            else:
                st.markdown(f"### {title}")
            
            # Article summary
            summary = article.get('summary', 'No summary available')
            st.markdown(f"*{summary}*")
            
            # Article metadata in columns
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                source = article.get('source', 'Unknown')
                st.markdown(f"**Source:** {source}")
            with col2:
                published_at = article.get('published_at', 'Unknown')
                if isinstance(published_at, str):
                    st.markdown(f"**Published:** {published_at}")
                else:
                    st.markdown(f"**Published:** {published_at.strftime('%Y-%m-%d %H:%M UTC')}")
            with col3:
                category = article.get('category', 'General')
                st.markdown(f"**Category:** {category}")
            
            # Why it matters section
            why_it_matters = article.get('why_it_matters', '')
            if why_it_matters and why_it_matters != 'Analysis not available':
                st.markdown(f"**Why it matters:** {why_it_matters}")
            
            # Metrics in a compact format
            col1, col2 = st.columns(2)
            with col1:
                importance = article.get('importance_score', 0)
                st.metric("Importance", f"{importance:.2f}", delta=None, delta_color="normal")
            with col2:
                sentiment = article.get('sentiment_score', 0)
                sentiment_color = "normal"
                if sentiment > 0.3:
                    sentiment_color = "inverse"
                elif sentiment < -0.3:
                    sentiment_color = "off"
                st.metric("Sentiment", f"{sentiment:.2f}", delta=None, delta_color=sentiment_color)

def display_ai_trends_summary():
    """Display AI trends summary"""
    st.subheader("🤖 AI Trends Summary")
    st.markdown("*Executive insights for AI leaders and decision-makers*")
    
    # Fetch AI trends summary
    trends_summary = fetch_ai_trends()
    if trends_summary:
        # Process reference links to make them clickable
        processed_summary = process_reference_links(trends_summary)
        
        # Display the structured summary with proper markdown and HTML rendering
        st.markdown(processed_summary, unsafe_allow_html=True)
        
        # Add a refresh button for trends
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Refresh", key="refresh_trends", help="Update AI trends summary"):
                st.rerun()
        with col2:
            st.caption("Last updated: " + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    else:
        st.warning("Unable to fetch AI trends summary at this time.")
        st.info("The AI trends summary provides executive-level insights on strategic developments, technology breakthroughs, and actionable recommendations for AI leaders.")

def process_reference_links(text: str) -> str:
    """Convert reference numbers like [1], [2] to clickable links with tooltips"""
    # Pattern to match reference numbers like [1], [2], etc.
    pattern = r'\[(\d+)\]'
    
    def replace_reference(match):
        ref_num = match.group(1)
        # Create a clickable link with tooltip
        return f'<a href="#ref-{ref_num}" style="color: #00ACB5; text-decoration: none; font-weight: bold;" title="Click to view reference {ref_num}">[{ref_num}]</a>'
    
    # Replace all reference numbers with clickable links
    processed_text = re.sub(pattern, replace_reference, text)
    
    # Add a references section at the end if there are any references
    references = re.findall(pattern, text)
    if references:
        processed_text += "\n\n---\n\n**📚 References:**\n"
        for ref_num in sorted(set(references), key=int):
            processed_text += f'<div id="ref-{ref_num}" style="margin: 10px 0; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #00ACB5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
            processed_text += f'<strong style="color: #00ACB5;">[{ref_num}]</strong> - <em>Reference {ref_num}</em><br>'
            processed_text += f'<small style="color: #A0A0A0; display: block; margin-top: 5px;">📖 Click the numbered link above to view this reference in context</small>'
            processed_text += '</div>\n'
    
    return processed_text

def refresh_token_usage():
    """Refresh token usage data"""
    try:
        new_usage = fetch_token_usage()
        if new_usage:
            st.session_state.token_usage = new_usage
            return True
    except Exception as e:
        logger.error(f"Error refreshing token usage: {str(e)}")
    return False

def display_all_articles():
    """Display all news articles in organized sections"""
    st.subheader("📰 News Articles")
    
    # Display news sections in order of importance
    display_news_articles(st.session_state.news_data.get('breaking', []), "Breaking")
    display_news_articles(st.session_state.news_data.get('top', []), "Top Stories")
    display_news_articles(st.session_state.news_data.get('funding', []), "Funding & M&A")
    display_news_articles(st.session_state.news_data.get('research', []), "Research & Innovation")

def display_analysis(analysis: Optional[str]):
    """Display news analysis"""
    st.subheader("News Analysis")
    if not analysis:
        st.warning("No analysis available at this time.")
        return
        
    st.markdown(analysis)

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

class LogHandler(logging.Handler):
    def __init__(self, max_logs=1000):
        super().__init__()
        self.log_buffer = []
        self.max_logs = max_logs
        self.log_queue = Queue()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        # Add initial log message
        self.emit(logging.LogRecord(
            name=__name__,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="Log handler initialized",
            args=(),
            exc_info=None
        ))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
            self.log_buffer.append(msg)
            if len(self.log_buffer) > self.max_logs:
                self.log_buffer.pop(0)
        except Exception as e:
            print(f"Error in log handler: {str(e)}")  # Fallback error logging
            self.handleError(record)

# Initialize the log handler
log_handler = LogHandler()
logging.getLogger().addHandler(log_handler)

def fetch_logs() -> List[str]:
    """Fetch new logs from the queue"""
    logs = []
    try:
        while not log_handler.log_queue.empty():
            logs.append(log_handler.log_queue.get())
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
    return logs

def display_logs():
    """Display logs in a streaming format"""
    st.subheader("Application Logs")
    
    # Create a container for logs
    log_container = st.empty()
    
    # Update logs from the log handler
    try:
        new_logs = fetch_logs()
        if new_logs:
            st.session_state.logs.extend(new_logs)
            # Keep only the last 1000 logs
            if len(st.session_state.logs) > 1000:
                st.session_state.logs = st.session_state.logs[-1000:]
            st.session_state.last_log_update = datetime.now(timezone.utc)
    except Exception as e:
        logger.error(f"Error updating logs: {str(e)}")
    
    # Display current logs
    log_container.code("\n".join(st.session_state.logs), language="text")
    
    # Add a clear logs button
    if st.button("Clear Logs"):
        st.session_state.logs = []
        log_container.code("", language="text")
        logger.info("Logs cleared")

def main():
    st.set_page_config(
        page_title="Below the Fold | AI Brief",
        page_icon="📰",
        layout="wide"
    )

    # Apply custom theme
    apply_custom_theme()

    # Initialize session state
    initialize_session_state()

    st.title("Below the Fold - Tech News Dashboard")
    
    # Add update controls in a sidebar
    with st.sidebar:
        st.subheader("Update Settings")
        selected_interval = st.selectbox(
            "Update Frequency",
            options=list(UPDATE_INTERVALS.keys()),
            index=list(UPDATE_INTERVALS.keys()).index("1 hour"),
            key="update_frequency"
        )
        
        # Update the interval in session state when selection changes
        if st.session_state.update_interval != UPDATE_INTERVALS[selected_interval]:
            st.session_state.update_interval = UPDATE_INTERVALS[selected_interval]
            current_time = datetime.now(timezone.utc)
            st.session_state.next_update = current_time + timedelta(seconds=UPDATE_INTERVALS[selected_interval])
            logger.info(f"Update interval changed to {selected_interval}")
        
        # Display last update time and next update time
        if st.session_state.last_update:
            st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if st.session_state.next_update:
            st.caption(f"Next update: {st.session_state.next_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Add manual refresh button
        if st.button("Refresh Now"):
            logger.info("Manual refresh requested")
            current_time = datetime.now(timezone.utc)
            news_data = {}
            for category in ['breaking', 'top', 'funding', 'research']:
                articles = fetch_news(category)
                if articles:
                    news_data[category] = articles
            if news_data:
                st.session_state.news_data = news_data
                st.session_state.last_update = current_time
                st.session_state.next_update = current_time + timedelta(seconds=st.session_state.update_interval)
            st.rerun()
    
    # Check for scheduled updates
    if check_for_updates():
        st.rerun()
    
    # Create tabs for all content
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Trends", "📰 News Feed", "💰 Tokens", "📊 Logs"])
    
    with tab1:
        display_ai_trends_summary()
    
    with tab2:
        display_all_articles()
    
    with tab3:
        display_token_usage(st.session_state.token_usage)
    
    with tab4:
        display_logs()

if __name__ == "__main__":
    try:
        logger.info("Starting dashboard application")
        main()
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}") 