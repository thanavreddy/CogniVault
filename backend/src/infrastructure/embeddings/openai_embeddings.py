import os
import asyncio
from typing import List
from openai import AsyncOpenAI
import time

class OpenAIEmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.batch_size = 100

    async def embed_text(self, text: str) -> List[float]:
        try:
            start_time = time.time()
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            # In a real scenario we might track usage and latency
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Error generating embedding: {str(e)}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings.extend([data.embedding for data in response.data])
            except Exception as e:
                # Basic retry could be added here
                raise RuntimeError(f"Error generating batch embeddings: {str(e)}")
            
            # Rate limiting protection
            if i + self.batch_size < len(texts):
                await asyncio.sleep(0.5)
                
        return embeddings
