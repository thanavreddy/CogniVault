import os
from enum import Enum
from typing import Dict

class QueryComplexity(str, Enum):
    SIMPLE = "SIMPLE"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    COMPLEX_REASONING = "COMPLEX_REASONING"

class ModelRouter:
    def __init__(self):
        self.model_gpt4_mini = os.getenv("MODEL_GPT4_MINI", "gpt-4o-mini")
        self.model_gpt4 = os.getenv("MODEL_GPT4", "gpt-4o")
        self.model_claude = os.getenv("MODEL_CLAUDE", "claude-3-7-sonnet-latest")
        
        # Prices per 1k tokens (approximate)
        self.pricing = {
            self.model_gpt4_mini: {"input": 0.00015, "output": 0.0006},
            self.model_gpt4: {"input": 0.005, "output": 0.015},
            self.model_claude: {"input": 0.003, "output": 0.015}
        }

    def estimate_complexity(self, query: str, context_length: int) -> QueryComplexity:
        words = len(query.split())
        
        # Simple heuristics for routing
        if "analyze" in query.lower() or "compare" in query.lower() or words > 50:
            return QueryComplexity.COMPLEX_REASONING
        elif context_length > 0 or words > 15:
            return QueryComplexity.KNOWLEDGE_SEARCH
        else:
            return QueryComplexity.SIMPLE

    def get_model(self, complexity: QueryComplexity) -> str:
        if complexity == QueryComplexity.SIMPLE:
            return self.model_gpt4_mini
        elif complexity == QueryComplexity.KNOWLEDGE_SEARCH:
            return self.model_gpt4
        else:
            return self.model_claude

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return 0.0
            
        prices = self.pricing[model]
        input_cost = (input_tokens / 1000.0) * prices["input"]
        output_cost = (output_tokens / 1000.0) * prices["output"]
        
        return input_cost + output_cost
