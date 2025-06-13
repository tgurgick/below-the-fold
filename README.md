# Below the Fold - Tech News Dashboard

A real-time dashboard for tracking and analyzing technology and AI news using the Perplexity API.

## Features

- Real-time tech news aggregation
- AI-powered news analysis
- Sentiment analysis and trend tracking
- Token usage monitoring
- Interactive visualizations
- Dark mode UI

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

## Project Structure

```
below-the-fold/
├── src/
│   ├── agents/
│   │   └── perplexity_agent.py
│   ├── config/
│   │   └── prompts.yaml
│   ├── models/
│   │   └── news.py
│   ├── utils/
│   │   └── token_calculator.py
│   ├── dashboard.py
│   └── main.py
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 