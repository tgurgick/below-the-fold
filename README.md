# Below the Fold - Tech News Dashboard

A real-time dashboard for tracking and analyzing technology and AI news using the Perplexity API. Built with FastAPI backend and Streamlit frontend, featuring AI-powered news aggregation, sentiment analysis, and executive-level insights with intelligent citation management.

## Features

- **Real-time tech news aggregation** from multiple categories
- **AI-powered news analysis** using Perplexity's Sonar model
- **Executive-level AI trends summaries** for business leaders
- **Strategic action items** with source citations
- **Sentiment analysis and trend tracking**
- **Token usage monitoring** with accurate cost tracking
- **Interactive visualizations** and dark mode UI
- **Structured news categorization** (Breaking, Top Stories, Funding, Research)
- **Intelligent citation system** with clickable source links

## System Architecture

### Agent Interaction Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    ┌──────────────────┐    │   Perplexity    │
│   Dashboard     │◄──►│   FastAPI        │◄──►│   API (Sonar)   │
└─────────────────┘    │   Backend        │    └─────────────────┘
         │              └──────────────────┘             │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   News Display  │    │   Newsroom       │    │   News Articles │
│   & Analytics   │    │   Coordinator    │    │   & Analysis    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agent Hierarchy & Collaboration

#### 1. **PerplexityAgent** - Core AI Interface
- **Role**: Primary interface to Perplexity's Sonar model
- **Responsibilities**:
  - Handles all API calls to Perplexity's Sonar model
  - Manages token usage tracking and cost calculation
  - Processes structured JSON responses
  - Validates news article data
  - Generates executive action items with citations
- **Key Methods**:
  - `get_news()`: Fetches categorized news with analysis
  - `get_ai_trends_summary()`: Generates executive insights
  - `get_executive_action_items()`: Creates strategic action items
  - `_calculate_tokens()`: Tracks usage and costs

#### 2. **Newsroom** - Orchestration Layer
- **Role**: Coordinates multiple specialized news agents
- **Responsibilities**:
  - Manages caching and update scheduling
  - Handles parallel news fetching
  - Routes requests to appropriate specialized agents
  - Ensures data consistency across agents
- **Collaboration**: Works with all specialized agents to provide unified news access

#### 3. **Specialized News Agents** - Domain Experts
Each agent is optimized for specific news categories and collaborates with PerplexityAgent:

- **BreakingNewsAgent**: Latest urgent developments (24h)
  - Focuses on time-sensitive, high-impact news
  - Uses specialized prompts for urgency detection
  
- **TopStoriesAgent**: Most significant stories (7 days)
  - Curates stories with lasting impact
  - Prioritizes industry-shaping developments
  
- **FundingAgent**: M&A, funding rounds, financial news
  - Tracks financial movements and market changes
  - Analyzes investment trends and valuations
  
- **ResearchAgent**: Technical breakthroughs and research
  - Monitors scientific and technical innovations
  - Focuses on breakthrough technologies

#### 4. **TokenCalculator** - Usage Tracking
- **Role**: Monitors and analyzes API usage
- **Responsibilities**:
  - Tracks token consumption with Sonar model pricing
  - Provides cost analytics and usage history
  - Helps optimize API usage efficiency

### Data Flow & Agent Collaboration

```
1. User Request → Dashboard
2. Dashboard → FastAPI Endpoint
3. FastAPI → Newsroom Coordinator
4. Newsroom → Specialized Agents (parallel execution)
5. Specialized Agents → PerplexityAgent
6. PerplexityAgent → Perplexity API (Sonar)
7. Response flows back through the chain
8. Data is processed, validated, and displayed
```

### Citation System Architecture

The system implements an intelligent citation management system:

#### Citation Processing Flow
```
1. PerplexityAgent generates content with citations
2. Citation extraction function parses Perplexity-style citations
3. URLs are extracted and validated
4. Reference numbers become clickable links
5. Links open source URLs in new tabs
```

#### Citation Format
- **Input**: Perplexity-style citations `[1] Source Name - Title (URL)`
- **Output**: Clickable reference numbers linking to source URLs
- **Display**: Clean, professional formatting without citation sections

#### Citation Integration
- **Trends Tab**: Executive summaries with source citations
- **Executive Tab**: Strategic action items with verified sources
- **News Feed**: Articles with source attribution
- **Risk Matrix**: Risk assessments with supporting sources

## Model Configuration

### Perplexity Sonar Model
- **Model**: `sonar` (Perplexity's latest and most capable model)
- **Cost**: $0.0003 per 1K tokens (input + output)
- **Capabilities**: Advanced reasoning, structured output, executive analysis
- **Use Cases**: News aggregation, trend analysis, AI insights, citation generation

### Prompt Engineering
The system uses carefully crafted prompts for different news categories:

- **Breaking News**: Urgent, time-sensitive developments
- **Top Stories**: Most significant stories from the past week
- **Funding News**: M&A, funding rounds, financial developments
- **Research News**: Technical breakthroughs and innovations
- **AI Trends Summary**: Executive-level insights with citations
- **Executive Action Items**: Strategic recommendations with source verification

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
- `GET /executive-action-items` - Strategic action items with citations

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
- **Core Functionality**: Handles all Perplexity API interactions
- **Model Usage**: Uses Sonar model for optimal performance
- **Data Processing**: Manages structured JSON parsing and validation
- **Usage Tracking**: Tracks token usage and costs
- **Citation Management**: Generates and processes source citations
- **Executive Insights**: Creates strategic action items and trends summaries

### Newsroom
- **Coordination**: Manages multiple news agents efficiently
- **Caching**: Implements intelligent caching for performance
- **Scheduling**: Handles update scheduling and parallel fetching
- **Data Flow**: Ensures consistent data across all agents

### Specialized Agents
Each agent collaborates with PerplexityAgent and is optimized for specific news categories:

- **BreakingNewsAgent**: Real-time urgent developments with immediate impact
- **TopStoriesAgent**: Curated significant stories with lasting importance
- **FundingAgent**: Financial and M&A news with market analysis
- **ResearchAgent**: Technical innovations and breakthrough technologies

### Dashboard Features
- **Trends Tab**: Executive AI insights with source citations
- **Executive Tab**: Strategic action items with verified sources
- **News Feed**: Categorized news articles with analysis and citations
- **Tokens Tab**: Usage monitoring and cost tracking
- **Logs Tab**: Real-time application logs

## Agent Collaboration Patterns

### 1. **Sequential Processing**
- Newsroom → Specialized Agent → PerplexityAgent → API
- Ensures proper data flow and error handling

### 2. **Parallel Execution**
- Multiple specialized agents can run simultaneously
- Newsroom coordinates parallel requests for efficiency

### 3. **Data Validation Chain**
- Each agent validates data before passing to next
- PerplexityAgent ensures API response quality
- Dashboard validates final display data

### 4. **Citation Integration**
- PerplexityAgent generates citations in content
- Citation extraction processes and validates URLs
- Dashboard displays clickable source links

### 5. **Error Handling**
- Each agent implements proper error handling
- Failures are gracefully handled and logged
- System remains functional even if individual agents fail

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 