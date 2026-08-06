import os
import time
from typing import List, Dict, Any, AsyncGenerator
from anthropic import AsyncAnthropic
from src.infrastructure.llm.openai_client import LLMResponse

class AnthropicLLMClient:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        start_time = time.time()
        
        # Convert standard messages format to Anthropic format
        system_msg = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
                
        try:
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": anthropic_messages
            }
            if system_msg:
                kwargs["system"] = system_msg
                
            response = await self.client.messages.create(**kwargs)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=response.content[0].text,
                model=model,
                usage=usage,
                cost=0.0,  # Would use router logic
                latency_ms=latency_ms
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API Error: {str(e)}")
