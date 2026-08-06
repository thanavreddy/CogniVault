import os
import time
from typing import List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from openai import AsyncOpenAI

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    cost: float
    latency_ms: int

class OpenAILLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Cost calculation would ideally use ModelRouter here
            cost = 0.0 
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                usage=usage,
                cost=cost,
                latency_ms=latency_ms
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {str(e)}")

    async def stream_complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI Stream Error: {str(e)}")
