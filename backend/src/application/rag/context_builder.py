"""Context Builder — assembles the optimal LLM context window.

Instead of dumping all retrieved chunks into the prompt, this module
intelligently assembles context from:
  - Conversation history (recent messages)
  - Retrieved document chunks (ranked by relevance)
  - System instructions
  - User profile / workspace settings
  - Few-shot examples (optional)

All within a strict token budget.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import tiktoken

from src.infrastructure.vector_store.qdrant_client import SearchResult
from src.domain.entities.conversation import Message, MessageRole

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Enterprise AI Knowledge Assistant. Your role is to help employees find accurate information from their company's internal documents.

Core principles:
1. GROUNDED: Only answer based on the provided context. Never make up information.
2. CITED: Always cite specific documents when making claims.
3. PRECISE: Be specific and concrete. Avoid vague statements.
4. HONEST: If the context doesn't contain enough information, clearly say so.
5. STRUCTURED: Use markdown formatting for clarity (headers, bullet points, tables).

Context format:
- Each context chunk is labeled [Source N: Document Title, Page X]
- Reference sources using their label when making claims.

If you cannot answer based on the provided context, respond:
"I don't have enough information in the available documents to answer this question accurately. Please try uploading relevant documents or refining your question."
"""


@dataclass
class ContextPackage:
    """The assembled context package ready to send to an LLM."""
    system_prompt: str
    messages: list[dict]  # Provider-neutral chat messages
    retrieved_chunks: list[SearchResult]
    total_tokens: int
    context_tokens: int
    history_tokens: int
    chunks_used: int
    chunks_available: int


class ContextBuilder:
    """Assembles an LLM context package within a token budget."""

    def __init__(
        self,
        max_tokens: int = 8000,
        history_token_budget: int = 2000,
        encoding_name: str = "cl100k_base",
    ) -> None:
        self.max_tokens = max_tokens
        self.history_token_budget = history_token_budget
        
        try:
            self._encoder = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._encoder = None

    def _count_tokens(self, text: str) -> int:
        if self._encoder:
            return len(self._encoder.encode(text))
        return len(text) // 4

    def _format_chunk_for_context(self, chunk: SearchResult, index: int) -> str:
        """Format a retrieved chunk as a labeled source block."""
        page_info = f", Page {chunk.page_number}" if chunk.page_number else ""
        header = f"[Source {index + 1}: {chunk.document_title or 'Document'}{page_info}]"
        return f"{header}\n{chunk.content}"

    def _trim_history(
        self,
        history: list[Message],
        token_budget: int,
    ) -> list[dict]:
        """Select the most recent history messages that fit within budget."""
        messages = []
        tokens_used = 0
        
        # Iterate in reverse (most recent first)
        for msg in reversed(history):
            msg_dict = {"role": msg.role.value.lower(), "content": msg.content}
            msg_tokens = self._count_tokens(msg.content) + 10  # Overhead per message
            
            if tokens_used + msg_tokens > token_budget:
                break
            
            messages.insert(0, msg_dict)
            tokens_used += msg_tokens
        
        logger.debug("History: %d/%d messages fit in %d tokens", len(messages), len(history), token_budget)
        return messages

    def build(
        self,
        query: str,
        retrieved_chunks: list[SearchResult],
        conversation_history: list[Message] | None = None,
        workspace_settings: dict | None = None,
        system_prompt_override: str | None = None,
    ) -> ContextPackage:
        """Build an optimized context package."""
        history = conversation_history or []
        system = system_prompt_override or SYSTEM_PROMPT
        
        # ── Token budget allocation ──────────────────────────────────────────
        system_tokens = self._count_tokens(system)
        query_tokens = self._count_tokens(query)
        reserved_output = 1500  # Reserve tokens for LLM response
        
        available = self.max_tokens - system_tokens - query_tokens - reserved_output
        history_budget = min(self.history_token_budget, available // 3)
        context_budget = available - history_budget
        
        # ── Conversation history ──────────────────────────────────────────────
        history_messages = self._trim_history(
            [m for m in history if m.role != MessageRole.SYSTEM],
            history_budget,
        )
        history_tokens = sum(self._count_tokens(m["content"]) for m in history_messages)
        
        # ── Retrieved chunks ─────────────────────────────────────────────────
        context_parts = []
        chunks_used = 0
        context_tokens = 0
        
        for i, chunk in enumerate(retrieved_chunks):
            formatted = self._format_chunk_for_context(chunk, i)
            chunk_tokens = self._count_tokens(formatted)
            
            if context_tokens + chunk_tokens > context_budget:
                logger.debug(
                    "Context budget reached at chunk %d/%d (%d/%d tokens)",
                    i, len(retrieved_chunks), context_tokens, context_budget,
                )
                break
            
            context_parts.append(formatted)
            context_tokens += chunk_tokens
            chunks_used += 1
        
        # ── Assemble final messages ───────────────────────────────────────────
        if context_parts:
            context_block = "\n\n".join(context_parts)
            user_content = (
                f"<context>\n{context_block}\n</context>\n\n"
                f"Question: {query}"
            )
        else:
            user_content = (
                f"Note: No relevant documents were found for this query.\n\n"
                f"Question: {query}"
            )
        
        messages = [
            *history_messages,
            {"role": "user", "content": user_content},
        ]
        
        total_tokens = system_tokens + history_tokens + context_tokens + query_tokens
        
        logger.info(
            "Context built: %d chunks used, %d total tokens (history=%d, context=%d)",
            chunks_used, total_tokens, history_tokens, context_tokens,
        )
        
        return ContextPackage(
            system_prompt=system,
            messages=messages,
            retrieved_chunks=retrieved_chunks[:chunks_used],
            total_tokens=total_tokens,
            context_tokens=context_tokens,
            history_tokens=history_tokens,
            chunks_used=chunks_used,
            chunks_available=len(retrieved_chunks),
        )
