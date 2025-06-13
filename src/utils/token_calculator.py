from typing import Dict, List
import tiktoken
from datetime import datetime

class TokenCalculator:
    def __init__(self):
        # Initialize the tokenizer
        self.encoding = tiktoken.get_encoding("cl100k_base")  # Perplexity uses GPT-4 tokenizer
        # Perplexity API costs (as of 2024)
        self.COST_PER_1K_TOKENS = {
            "pplx-7b-online": 0.0001,  # $0.0001 per 1K tokens
        }
        self.total_tokens = 0
        self.total_cost = 0.0
        self.usage_history: List[Dict] = []

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self.encoding.encode(text))

    def calculate_cost(self, tokens: int, model: str = "pplx-7b-online") -> float:
        """Calculate the cost for a given number of tokens."""
        cost_per_1k = self.COST_PER_1K_TOKENS.get(model, 0.0001)  # Default to pplx-7b-online cost
        return (tokens / 1000) * cost_per_1k

    def add_usage(self, prompt: str, response: str, model: str = "pplx-7b-online"):
        """Add a new usage record and update totals."""
        prompt_tokens = self.count_tokens(prompt)
        response_tokens = self.count_tokens(response)
        total_tokens = prompt_tokens + response_tokens
        cost = self.calculate_cost(total_tokens, model)

        # Update totals
        self.total_tokens += total_tokens
        self.total_cost += cost

        # Add to history
        self.usage_history.append({
            "timestamp": datetime.now(),
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "model": model
        })

    def get_usage_summary(self) -> Dict:
        """Get a summary of token usage and costs."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "last_updated": datetime.now(),
            "usage_history": self.usage_history
        }

    def reset(self):
        """Reset the calculator."""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.usage_history = [] 