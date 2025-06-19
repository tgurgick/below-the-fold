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
        logger.info(f"Dashboard: Fetching {category} news from API")
        response = requests.get(f"{API_BASE_URL}/news/{category}")
        response.raise_for_status()
        data = response.json()
        articles = data.get('articles', [])
        logger.info(f"Dashboard: Successfully fetched {len(articles)} {category} articles")
        return articles
    except requests.exceptions.ConnectionError:
        logger.error(f"Dashboard: Could not connect to the API server for {category} news")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"Dashboard: HTTP error occurred fetching {category} news: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Dashboard: Error fetching {category} news: {str(e)}")
        return []

def fetch_analysis() -> Optional[str]:
    """Fetch news analysis"""
    try:
        logger.info("Dashboard: Fetching news analysis from API")
        response = requests.get(f"{API_BASE_URL}/news/analyze")
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            logger.error(f"Dashboard: API returned error for analysis: {data['error']}")
            return None
        analysis = data.get('analysis')
        if not analysis:
            logger.warning("Dashboard: No analysis data received")
            return None
        logger.info("Dashboard: Successfully fetched news analysis")
        return analysis
    except requests.exceptions.ConnectionError:
        logger.error("Dashboard: Could not connect to the API server for analysis")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Dashboard: HTTP error occurred fetching analysis: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Dashboard: Error fetching analysis: {str(e)}")
        return None

def fetch_token_usage() -> Dict:
    """Fetch token usage statistics from the API"""
    try:
        logger.info("Dashboard: Fetching token usage from API")
        response = requests.get(f"{API_BASE_URL}/usage")
        response.raise_for_status()
        usage_data = response.json()
        logger.info(f"Dashboard: Successfully fetched token usage - {usage_data.get('total_tokens', 0)} tokens, ${usage_data.get('total_cost', 0):.4f} cost")
        return usage_data
    except requests.exceptions.ConnectionError:
        logger.error(f"Dashboard: Could not connect to API server at {API_BASE_URL} for token usage")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Dashboard: HTTP error occurred fetching token usage: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Dashboard: Error fetching token usage: {str(e)}")
        return None

def fetch_ai_trends() -> Optional[str]:
    """Fetch AI trends summary from the API"""
    try:
        logger.info("Dashboard: Fetching AI trends summary from API")
        response = requests.get(f"{API_BASE_URL}/ai-trends")
        response.raise_for_status()
        data = response.json()
        summary = data.get('summary')
        if not summary:
            logger.warning("Dashboard: No AI trends summary received")
            return None
        logger.info("Dashboard: Successfully fetched AI trends summary")
        return summary
    except requests.exceptions.ConnectionError:
        logger.error("Dashboard: Could not connect to the API server for AI trends")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Dashboard: HTTP error occurred fetching AI trends: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Dashboard: Error fetching AI trends: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    logger.info("Dashboard: Initializing session state")
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
    logger.info("Dashboard: Session state initialized successfully")

def check_for_updates():
    """Check if it's time to update the data"""
    current_time = datetime.now(timezone.utc)
    
    # Ensure next_update is set
    if not st.session_state.next_update:
        st.session_state.next_update = current_time + timedelta(seconds=st.session_state.update_interval)
        logger.info("Dashboard: Next update time initialized")
        return False
        
    if current_time >= st.session_state.next_update:
        logger.info("Dashboard: Scheduled update triggered")
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
            
            logger.info(f"Dashboard: Scheduled update completed - {sum(len(articles) for articles in news_data.values())} total articles")
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
        logger.info("Dashboard: Refreshing token usage data")
        new_usage = fetch_token_usage()
        if new_usage:
            st.session_state.token_usage = new_usage
            logger.info("Dashboard: Token usage refreshed successfully")
            return True
    except Exception as e:
        logger.error(f"Dashboard: Error refreshing token usage: {str(e)}")
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

def display_executive_dashboard():
    """Display executive-focused dashboard with action items and risk matrix"""
    # Fetch AI trends summary for action items
    trends_summary = fetch_ai_trends()
    
    # Create risk matrix data
    risk_matrix_data = create_risk_matrix()
    
    # Main content in a single column for better scrolling
    
    # Executive Summary with Key Metrics
    st.subheader("📈 Executive Summary")
    
    # Get current news data for summary
    if st.session_state.news_data:
        total_articles = sum(len(articles) for articles in st.session_state.news_data.values())
        breaking_count = len(st.session_state.news_data.get('breaking', []))
        funding_count = len(st.session_state.news_data.get('funding', []))
        research_count = len(st.session_state.news_data.get('research', []))
        
        # Calculate sentiment and importance
        all_articles = []
        for category, articles in st.session_state.news_data.items():
            all_articles.extend(articles)
        
        avg_sentiment = 0
        avg_importance = 0
        ai_articles_count = 0
        
        if all_articles:
            avg_sentiment = sum(article.get('sentiment_score', 0) for article in all_articles) / len(all_articles)
            avg_importance = sum(article.get('importance_score', 0) for article in all_articles) / len(all_articles)
            ai_articles_count = len([a for a in all_articles if 'ai' in a.get('title', '').lower() or 'ai' in a.get('category', '').lower()])
        
        # Display metrics in a clean grid
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", total_articles)
        with col2:
            st.metric("Breaking News", breaking_count)
        with col3:
            st.metric("Funding Events", funding_count)
        with col4:
            st.metric("Research Updates", research_count)
        
        # Second row of metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sentiment_color = "normal"
            if avg_sentiment > 0.3:
                sentiment_color = "inverse"
            elif avg_sentiment < -0.3:
                sentiment_color = "off"
            st.metric("Market Sentiment", f"{avg_sentiment:.2f}", delta=None, delta_color=sentiment_color)
        with col2:
            st.metric("Average Importance", f"{avg_importance:.2f}")
        with col3:
            st.metric("AI-Focused Articles", ai_articles_count)
        with col4:
            if st.session_state.token_usage:
                cost = st.session_state.token_usage.get('total_cost', 0)
                st.metric("API Cost", f"${cost:.4f}")
    
    st.markdown("---")
    
    # Action Items and Risk Matrix in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Strategic Action Items")
        if trends_summary:
            # Extract action items from the AI trends summary
            action_items = extract_action_items(trends_summary)
            if action_items:
                for i, item in enumerate(action_items, 1):
                    st.markdown(f"**{i}.** {item}")
            else:
                st.info("No specific action items found. Here are strategic recommendations:")
                # Fallback to general strategic recommendations
                strategic_recommendations = [
                    "Conduct comprehensive AI ethics review and framework implementation",
                    "Evaluate current AI talent pipeline and identify critical hiring needs",
                    "Assess regulatory compliance readiness for upcoming AI legislation",
                    "Review AI investment portfolio and identify new opportunities",
                    "Develop AI governance structure and decision-making processes"
                ]
                for i, rec in enumerate(strategic_recommendations, 1):
                    st.markdown(f"**{i}.** {rec}")
        else:
            st.info("Loading action items from AI trends analysis...")
            if st.button("🔄 Generate Action Items", key="generate_actions"):
                st.rerun()
    
    with col2:
        st.subheader("📊 Risk Matrix")
        display_simplified_risk_matrix(risk_matrix_data)
    
    st.markdown("---")
    
    # Strategic Insights
    st.subheader("🔍 Strategic Insights")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Market Trends**")
        st.markdown("• AI investment continues to accelerate")
        st.markdown("• Regulatory landscape evolving rapidly")
        st.markdown("• Talent competition intensifying")
        st.markdown("• Open source vs proprietary model debate intensifying")
        
    with col2:
        st.markdown("**Competitive Landscape**")
        st.markdown("• Major players consolidating")
        st.markdown("• Startup ecosystem thriving")
        st.markdown("• International competition growing")
        st.markdown("• Vertical AI solutions gaining traction")
    
    # Refresh button at the bottom
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Dashboard", key="refresh_executive_bottom", help="Update executive dashboard data"):
            st.rerun()
    with col2:
        st.caption("Last updated: " + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))

def display_simplified_risk_matrix(risk_data: Dict):
    """Display simplified 4-quadrant risk matrix with clickable quadrants"""
    opportunities = risk_data["opportunities"]
    
    # Create simplified 4-quadrant matrix
    matrix_html = """
    <style>
    .risk-matrix-4 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 10px;
        margin: 15px 0;
        height: 400px;
    }
    .quadrant {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        font-size: 12px;
        font-weight: bold;
        color: white;
        position: relative;
        cursor: pointer;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .quadrant:hover {
        transform: scale(1.02);
    }
    .quadrant-header {
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 8px;
        text-align: center;
    }
    .quadrant-content {
        font-size: 10px;
        line-height: 1.2;
        text-align: left;
        width: 100%;
        overflow-y: auto;
        max-height: 280px;
    }
    .opportunity-item {
        margin: 4px 0;
        padding: 3px;
        background: rgba(255,255,255,0.1);
        border-radius: 3px;
        font-weight: normal;
    }
    .low-risk-low-reward { background-color: #666; }
    .low-risk-high-reward { background-color: #4CAF50; }
    .high-risk-low-reward { background-color: #F44336; }
    .high-risk-high-reward { background-color: #FF9800; }
    .quadrant-count {
        position: absolute;
        top: 5px;
        right: 5px;
        background: rgba(0,0,0,0.3);
        border-radius: 50%;
        width: 25px;
        height: 25px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    </style>
    <div class="risk-matrix-4">
    """
    
    # Define quadrants with proper labels
    quadrants = [
        ("low-risk-low-reward", "Low Risk<br>Low Reward", "Low", "Low"),
        ("low-risk-high-reward", "Low Risk<br>High Reward", "Low", "High"),
        ("high-risk-low-reward", "High Risk<br>Low Reward", "High", "Low"),
        ("high-risk-high-reward", "High Risk<br>High Reward", "High", "High")
    ]
    
    for class_name, label, risk_level, reward_level in quadrants:
        # Get opportunities in this quadrant
        quadrant_opportunities = [opp for opp in opportunities if opp["risk_level"] == risk_level and opp["reward_level"] == reward_level]
        count = len(quadrant_opportunities)
        
        # Create content for this quadrant
        content_html = f'<div class="quadrant-header">{label}</div>'
        if quadrant_opportunities:
            content_html += '<div class="quadrant-content">'
            for opp in quadrant_opportunities[:3]:  # Show first 3 opportunities
                content_html += f'<div class="opportunity-item">• {opp["opportunity"]}</div>'
            if len(quadrant_opportunities) > 3:
                content_html += f'<div class="opportunity-item">... and {len(quadrant_opportunities) - 3} more</div>'
            content_html += '</div>'
        else:
            content_html += '<div class="quadrant-content">No opportunities</div>'
        
        matrix_html += f'<div class="quadrant {class_name}" onclick="showQuadrantDetails(\'{risk_level}-{reward_level}\')">{content_html}<div class="quadrant-count">{count}</div></div>'
    
    matrix_html += "</div>"
    
    # Add JavaScript for click handling
    matrix_html += """
    <script>
    function showQuadrantDetails(quadrant) {
        // This would trigger a Streamlit callback in a real implementation
        console.log('Clicked quadrant:', quadrant);
    }
    </script>
    """
    
    st.markdown(matrix_html, unsafe_allow_html=True)

def extract_action_items(trends_summary: str) -> List[str]:
    """Extract action items from AI trends summary"""
    action_items = []
    
    # Look for action items section
    if "Action Items for AI Leaders" in trends_summary:
        # Extract the action items section
        start_marker = "Action Items for AI Leaders"
        end_marker = "**Bottom Line**" if "**Bottom Line**" in trends_summary else None
        
        if end_marker:
            action_section = trends_summary.split(start_marker)[1].split(end_marker)[0]
        else:
            action_section = trends_summary.split(start_marker)[1]
        
        # Extract bullet points
        lines = action_section.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                # Clean up the action item
                item = line.lstrip('- ').lstrip('• ').strip()
                if item and len(item) > 10:  # Ensure it's a meaningful action item
                    action_items.append(item)
    
    return action_items

def create_risk_matrix() -> Dict:
    """Create dynamic risk matrix data based on current news and trends"""
    # Base opportunities that are always relevant
    base_opportunities = [
        {
            "opportunity": "Invest in Emerging AI Models",
            "risk_level": "High",
            "reward_level": "High",
            "description": "Early investment in next-gen AI models",
            "timeframe": "6-12 months",
            "category": "Technology"
        },
        {
            "opportunity": "Acquire AI Talent",
            "risk_level": "Medium",
            "reward_level": "High",
            "description": "Strategic hiring of AI specialists",
            "timeframe": "3-6 months",
            "category": "Talent"
        },
        {
            "opportunity": "Regulatory Compliance",
            "risk_level": "Low",
            "reward_level": "Medium",
            "description": "Proactive compliance with AI regulations",
            "timeframe": "1-3 months",
            "category": "Compliance"
        },
        {
            "opportunity": "AI Ethics Framework",
            "risk_level": "Low",
            "reward_level": "High",
            "description": "Implement comprehensive AI ethics",
            "timeframe": "3-6 months",
            "category": "Governance"
        },
        {
            "opportunity": "Partnership with AI Startups",
            "risk_level": "Medium",
            "reward_level": "Medium",
            "description": "Strategic partnerships with emerging AI companies",
            "timeframe": "6-12 months",
            "category": "Partnerships"
        }
    ]
    
    # Analyze current news data to add dynamic opportunities
    dynamic_opportunities = []
    
    if st.session_state.news_data:
        # Analyze breaking news for urgent opportunities
        breaking_news = st.session_state.news_data.get('breaking', [])
        if breaking_news:
            # Look for funding news, acquisitions, or major announcements
            for article in breaking_news:
                title = article.get('title', '').lower()
                if any(keyword in title for keyword in ['funding', 'acquisition', 'merger', 'investment']):
                    dynamic_opportunities.append({
                        "opportunity": f"Respond to {article.get('title', 'Market Development')}",
                        "risk_level": "Medium",
                        "reward_level": "High",
                        "description": f"Strategic response to: {article.get('summary', 'Market development')}",
                        "timeframe": "1-3 months",
                        "category": "Market Response",
                        "source": article.get('title', '')
                    })
        
        # Analyze funding news for investment opportunities
        funding_news = st.session_state.news_data.get('funding', [])
        if funding_news:
            for article in funding_news:
                title = article.get('title', '').lower()
                if any(keyword in title for keyword in ['startup', 'series', 'funding', 'valuation']):
                    dynamic_opportunities.append({
                        "opportunity": f"Evaluate Investment in {article.get('title', 'AI Startup')}",
                        "risk_level": "High",
                        "reward_level": "High",
                        "description": f"Investment opportunity: {article.get('summary', 'Startup funding')}",
                        "timeframe": "3-6 months",
                        "category": "Investment",
                        "source": article.get('title', '')
                    })
        
        # Analyze research news for technology opportunities
        research_news = st.session_state.news_data.get('research', [])
        if research_news:
            for article in research_news:
                title = article.get('title', '').lower()
                if any(keyword in title for keyword in ['breakthrough', 'innovation', 'research', 'new model']):
                    dynamic_opportunities.append({
                        "opportunity": f"Explore {article.get('title', 'Technology Innovation')}",
                        "risk_level": "Medium",
                        "reward_level": "High",
                        "description": f"Technology opportunity: {article.get('summary', 'Research breakthrough')}",
                        "timeframe": "6-12 months",
                        "category": "Technology",
                        "source": article.get('title', '')
                    })
    
    # Combine base and dynamic opportunities
    all_opportunities = base_opportunities + dynamic_opportunities[:3]  # Limit dynamic opportunities
    
    # Calculate risk/reward distribution
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    reward_counts = {"Low": 0, "Medium": 0, "High": 0}
    
    for opp in all_opportunities:
        risk_counts[opp["risk_level"]] += 1
        reward_counts[opp["reward_level"]] += 1
    
    return {
        "opportunities": all_opportunities,
        "risk_levels": ["Low", "Medium", "High"],
        "reward_levels": ["Low", "Medium", "High"],
        "risk_distribution": risk_counts,
        "reward_distribution": reward_counts,
        "total_opportunities": len(all_opportunities)
    }

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
    """Display logs in a streaming format with comprehensive filtering"""
    st.subheader("📊 System Logs & Activity")
    
    # Create filters for log types
    col1, col2, col3 = st.columns(3)
    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            key="log_level_filter"
        )
    with col2:
        log_source = st.selectbox(
            "Source",
            ["ALL", "API", "PerplexityAgent", "Newsroom", "BreakingNewsAgent", "TopStoriesAgent", "FundingAgent", "ResearchAgent", "Dashboard"],
            key="log_source_filter"
        )
    with col3:
        if st.button("🔄 Refresh Logs", key="refresh_logs"):
            st.rerun()
    
    # Create a container for logs
    log_container = st.empty()
    
    # Update logs from the log handler
    try:
        new_logs = fetch_logs()
        if new_logs:
            st.session_state.logs.extend(new_logs)
            # Keep only the last 2000 logs
            if len(st.session_state.logs) > 2000:
                st.session_state.logs = st.session_state.logs[-2000:]
            st.session_state.last_log_update = datetime.now(timezone.utc)
    except Exception as e:
        logger.error(f"Error updating logs: {str(e)}")
    
    # Filter logs based on user selection
    filtered_logs = []
    for log in st.session_state.logs:
        # Apply level filter
        if log_level != "ALL":
            if f" - {log_level} - " not in log:
                continue
        
        # Apply source filter
        if log_source != "ALL":
            if log_source not in log:
                continue
        
        filtered_logs.append(log)
    
    # Display log statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Logs", len(st.session_state.logs))
    with col2:
        st.metric("Filtered Logs", len(filtered_logs))
    with col3:
        api_calls = len([log for log in st.session_state.logs if "API Call:" in log])
        st.metric("API Calls", api_calls)
    with col4:
        errors = len([log for log in st.session_state.logs if "ERROR" in log])
        st.metric("Errors", errors)
    
    # Display current logs with syntax highlighting
    if filtered_logs:
        # Create a more readable format
        formatted_logs = []
        for log in filtered_logs[-100:]:  # Show last 100 filtered logs
            # Color code different log levels
            if "ERROR" in log:
                formatted_logs.append(f"🔴 {log}")
            elif "WARNING" in log:
                formatted_logs.append(f"🟡 {log}")
            elif "INFO" in log:
                formatted_logs.append(f"🔵 {log}")
            elif "DEBUG" in log:
                formatted_logs.append(f"⚪ {log}")
            else:
                formatted_logs.append(log)
        
        log_container.code("\n".join(formatted_logs), language="text")
    else:
        log_container.info("No logs match the current filters.")
    
    # Add a clear logs button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Logs"):
            st.session_state.logs = []
            log_container.code("", language="text")
            logger.info("Logs cleared by user")
    with col2:
        st.caption("Last updated: " + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    
    # Show recent activity summary
    st.subheader("📈 Recent Activity Summary")
    
    # Get recent logs for summary
    recent_logs = st.session_state.logs[-50:] if st.session_state.logs else []
    
    # Count different types of activities
    api_calls = [log for log in recent_logs if "API Call:" in log]
    agent_actions = [log for log in recent_logs if "PerplexityAgent:" in log or "Newsroom:" in log]
    errors = [log for log in recent_logs if "ERROR" in log]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recent API Calls", len(api_calls))
        if api_calls:
            st.caption("Last: " + api_calls[-1].split(" - ")[0] if api_calls else "")
    with col2:
        st.metric("Agent Actions", len(agent_actions))
        if agent_actions:
            st.caption("Last: " + agent_actions[-1].split(" - ")[0] if agent_actions else "")
    with col3:
        st.metric("Recent Errors", len(errors))
        if errors:
            st.caption("Last: " + errors[-1].split(" - ")[0] if errors else "")
    
    # Show recent API calls in a table
    if api_calls:
        st.subheader("🔄 Recent API Calls")
        api_data = []
        for log in api_calls[-10:]:  # Last 10 API calls
            parts = log.split(" - ")
            if len(parts) >= 3:
                timestamp = parts[0]
                endpoint = parts[2] if len(parts) > 2 else "Unknown"
                api_data.append({"Timestamp": timestamp, "Endpoint": endpoint})
        
        if api_data:
            st.dataframe(api_data, use_container_width=True)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Executive", "🤖 Trends", "📰 News Feed", "💰 Tokens", "📊 Logs"])
    
    with tab1:
        display_executive_dashboard()
    
    with tab2:
        display_ai_trends_summary()
    
    with tab3:
        display_all_articles()
    
    with tab4:
        display_token_usage(st.session_state.token_usage)
    
    with tab5:
        display_logs()

if __name__ == "__main__":
    try:
        logger.info("Starting dashboard application")
        main()
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}") 