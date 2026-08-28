"""Local Ollama chat provider used by the RAG and agent layers."""
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional, Sequence

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict
    cost: float
    latency_ms: float


class OllamaLLMClient:
    """Async Ollama client with retries and LangChain tool/structured-output support."""

    MAX_RETRIES = 3

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.default_model = settings.ollama_model

    def _model(self, model: str | None = None, temperature: float = 0.0) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=model or self.default_model,
            temperature=temperature,
            num_predict=settings.ollama_max_tokens,
        )

    @staticmethod
    def _messages(messages: list[dict], system_prompt: str = "") -> list[Any]:
        result: list[Any] = []
        if system_prompt:
            result.append(SystemMessage(content=system_prompt))
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
        return result

    @staticmethod
    def _usage(response: AIMessage) -> dict:
        metadata = response.response_metadata or {}
        usage_metadata = response.usage_metadata or {}
        prompt_tokens = usage_metadata.get("input_tokens", metadata.get("prompt_eval_count", 0))
        completion_tokens = usage_metadata.get("output_tokens", metadata.get("eval_count", 0))
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        response_format: Optional[dict] = None,
        system_prompt: str = "",
    ) -> LLMResponse:
        """Generate a response, raising an actionable error when Ollama is unavailable."""
        llm = self._model(model, temperature)
        if max_tokens != settings.ollama_max_tokens:
            llm = llm.bind(num_predict=max_tokens)
        if response_format:
            llm = llm.bind(format=response_format)

        for attempt in range(self.MAX_RETRIES):
            try:
                start = time.time()
                response = await llm.ainvoke(self._messages(messages, system_prompt))
                latency_ms = (time.time() - start) * 1000
                usage = self._usage(response)
                logger.info("Ollama complete: model=%s tokens=%d latency=%.0fms", model or self.default_model, usage["total_tokens"], latency_ms)
                return LLMResponse(
                    content=str(response.content),
                    model=model or self.default_model,
                    usage=usage,
                    cost=0.0,
                    latency_ms=latency_ms,
                )
            except Exception as exc:
                if attempt == self.MAX_RETRIES - 1:
                    raise RuntimeError(
                        f"Ollama generation failed for model '{model or self.default_model}' at "
                        f"'{self.base_url}'. Ensure Ollama is running and the model is installed "
                        f"(ollama serve && ollama pull {model or self.default_model})."
                    ) from exc
                logger.warning("Ollama request failed, retrying: %s", exc)

        raise RuntimeError("Ollama generation failed")

    async def stream_complete(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        """Stream generated content from Ollama."""
        llm = self._model(model, temperature).bind(num_predict=max_tokens)
        try:
            async for chunk in llm.astream(self._messages(messages, system_prompt)):
                if chunk.content:
                    yield str(chunk.content)
        except Exception as exc:
            raise RuntimeError(
                f"Ollama streaming failed for model '{model or self.default_model}'. "
                "Check that Ollama is running and the model is installed."
            ) from exc

    def bind_tools(self, tools: Sequence[Any], model: str | None = None, **kwargs: Any) -> Any:
        """Bind native tool schemas supported by the configured Ollama model."""
        return self._model(model, kwargs.pop("temperature", 0.0)).bind_tools(tools, **kwargs)

    def with_structured_output(self, schema: Any, model: str | None = None, **kwargs: Any) -> Any:
        """Return a LangChain runnable that parses Ollama output into the schema."""
        return self._model(model, kwargs.pop("temperature", 0.0)).with_structured_output(schema, **kwargs)
