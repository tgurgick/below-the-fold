# Below the Fold - Tech News Dashboard

A real-time dashboard for tracking and analyzing technology and AI news using the Perplexity API. Built with FastAPI backend and Streamlit frontend, featuring AI-powered news aggregation, sentiment analysis, and executive-level insights.

## Features

- **Real-time tech news aggregation** from multiple categories
- **AI-powered news analysis** using Perplexity's Sonar model
- **Executive-level AI trends summaries** for business leaders
- **Sentiment analysis and trend tracking**
- **Token usage monitoring** with accurate cost tracking
- **Interactive visualizations** and dark mode UI
- **Structured news categorization** (Breaking, Top Stories, Funding, Research)

## System Architecture

### Agent Interaction Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI        │    │   Perplexity    │
│   Dashboard     │◄──►│   Backend        │◄──►│   API (Sonar)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   News Display  │    │   Newsroom       │    │   News Articles │
│   & Analytics   │    │   Coordinator    │    │   & Analysis    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agent Hierarchy

1. **PerplexityAgent** - Core AI interface
   - Handles all API calls to Perplexity's Sonar model
   - Manages token usage tracking and cost calculation
   - Processes structured JSON responses
   - Validates news article data

2. **Newsroom** - Orchestration layer
   - Coordinates multiple specialized news agents
   - Manages caching and update scheduling
   - Handles parallel news fetching

3. **Specialized News Agents**:
   - **BreakingNewsAgent**: Latest urgent developments (24h)
   - **TopStoriesAgent**: Most significant stories (7 days)
   - **FundingAgent**: M&A, funding rounds, financial news
   - **ResearchAgent**: Technical breakthroughs and research

4. **TokenCalculator** - Usage tracking
   - Monitors API costs with Sonar model pricing
   - Tracks token usage history
   - Provides cost analytics

### Data Flow

```
1. User Request → Dashboard
2. Dashboard → FastAPI Endpoint
3. FastAPI → Newsroom Coordinator
4. Newsroom → Specialized Agents
5. Agents → PerplexityAgent
6. PerplexityAgent → Perplexity API (Sonar)
7. Response flows back through the chain
8. Data is processed, validated, and displayed
```

## Model Configuration

### Perplexity Sonar Model
- **Model**: `sonar` (Perplexity's latest and most capable model)
- **Cost**: $0.0003 per 1K tokens (input + output)
- **Capabilities**: Advanced reasoning, structured output, executive analysis
- **Use Cases**: News aggregation, trend analysis, AI insights

### Prompt Engineering
The system uses carefully crafted prompts for different news categories:
- **Breaking News**: Urgent, time-sensitive developments
- **Top Stories**: Most significant stories from the past week
- **Funding News**: M&A, funding rounds, financial developments
- **Research News**: Technical breakthroughs and innovations
- **AI Trends Summary**: Executive-level insights for business leaders

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/below-the-fold.git
cd below-the-fold
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Perplexity API key:
```
PERPLEXITY_API_KEY=your_api_key_here
```

## Running the Application

1. Start the API server:
```bash
python src/main.py
```

2. In a separate terminal, start the dashboard:
```bash
streamlit run src/dashboard.py
```

The dashboard will be available at `http://localhost:8501`

## API Endpoints

### News Endpoints
- `GET /news/breaking` - Latest breaking news
- `GET /news/top` - Top stories from the past week
- `GET /news/funding` - Funding and M&A news
- `GET /news/research` - Research and technical breakthroughs

### Analysis Endpoints
- `GET /news/analyze` - News trend analysis
- `GET /ai-trends` - Executive AI trends summary

### Utility Endpoints
- `GET /usage` - Token usage and cost statistics

## Project Structure

```
below-the-fold/
├── src/
│   ├── agents/
│   │   ├── perplexity_agent.py    # Core AI interface
│   │   └── news_agents.py         # Specialized news agents
│   ├── config/
│   │   ├── prompts.yaml           # AI prompt templates
│   │   └── loader.py              # Configuration loader
│   ├── models/
│   │   └── news.py                # Data models
│   ├── utils/
│   │   └── token_calculator.py    # Usage tracking
│   ├── dashboard.py               # Streamlit frontend
│   └── main.py                    # FastAPI backend
├── .env                           # Environment variables
├── .gitignore
├── README.md
└── requirements.txt
```

## Key Components

### PerplexityAgent
- Handles all Perplexity API interactions
- Uses Sonar model for optimal performance
- Manages structured JSON parsing and validation
- Tracks token usage and costs

### Newsroom
- Coordinates multiple news agents
- Manages caching and update scheduling
- Handles parallel news fetching for efficiency

### Specialized Agents
Each agent is optimized for specific news categories:
- **BreakingNewsAgent**: Real-time urgent developments
- **TopStoriesAgent**: Curated significant stories
- **FundingAgent**: Financial and M&A news
- **ResearchAgent**: Technical innovations

### Dashboard Features
- **Trends Tab**: Executive AI insights and summaries
- **News Feed**: Categorized news articles with analysis
- **Tokens Tab**: Usage monitoring and cost tracking
- **Logs Tab**: Real-time application logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 