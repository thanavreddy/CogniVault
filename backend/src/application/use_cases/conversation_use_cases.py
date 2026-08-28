"""Conversation and chat use cases."""
import logging
from uuid import UUID, uuid4

from src.domain.entities.conversation import Conversation, Message, MessageRole
from src.domain.repositories.conversation_repository import ConversationRepository
from src.application.rag.rag_pipeline import RAGPipeline, RAGResponse
from src.domain.entities.evaluation import EvaluationResult
from src.infrastructure.repositories.postgres_evaluation_repository import PostgresEvaluationRepository

logger = logging.getLogger(__name__)


class CreateConversationUseCase:
    def __init__(self, conversation_repo: ConversationRepository) -> None:
        self._repo = conversation_repo

    async def execute(
        self,
        workspace_id: UUID,
        user_id: str,
        title: str | None = None,
    ) -> Conversation:
        conversation = Conversation(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            title=title or "New Conversation",
        )
        return await self._repo.create(conversation)


class SendMessageUseCase:
    """Main RAG entry point — processes a user message and returns an AI response."""

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        rag_pipeline: RAGPipeline,
        evaluation_repo: PostgresEvaluationRepository | None = None,
    ) -> None:
        self._conv_repo = conversation_repo
        self._rag_pipeline = rag_pipeline
        self._eval_repo = evaluation_repo

    async def execute(
        self,
        content: str,
        workspace_id: UUID,
        user_id: str,
        conversation_id: UUID | None = None,
        document_ids: list[UUID] | None = None,
        force_model: str | None = None,
    ) -> tuple[Conversation, Message]:
        """Process a message and return the updated conversation and AI response."""
        # ── Get or create conversation ────────────────────────────────────────
        if conversation_id:
            conversation = await self._conv_repo.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
        else:
            conversation = Conversation(
                id=uuid4(),
                workspace_id=workspace_id,
                user_id=user_id,
                title=content[:60] + "..." if len(content) > 60 else content,
            )
            conversation = await self._conv_repo.create(conversation)

        # ── Save user message ─────────────────────────────────────────────────
        user_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=content,
        )
        await self._conv_repo.add_message(user_message)

        # ── Run RAG pipeline ──────────────────────────────────────────────────
        rag_response: RAGResponse = await self._rag_pipeline.run(
            query=content,
            workspace_id=str(workspace_id),
            conversation_history=conversation.messages,
            document_ids=[str(d) for d in document_ids] if document_ids else None,
            force_model=force_model,
        )

        # ── Save assistant message ────────────────────────────────────────────
        assistant_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=rag_response.answer,
            sources=rag_response.citations,
            token_count=rag_response.token_count,
            latency_ms=int(rag_response.latency_ms),
            model_used=rag_response.model_used,
            cost_usd=rag_response.cost_usd,
        )
        saved_message = await self._conv_repo.add_message(assistant_message)

        # ── Refresh conversation ──────────────────────────────────────────────
        updated_conversation = await self._conv_repo.get_by_id(conversation.id)

        return updated_conversation, saved_message


class GetConversationHistoryUseCase:
    def __init__(self, conversation_repo: ConversationRepository) -> None:
        self._repo = conversation_repo

    async def execute(
        self,
        workspace_id: UUID,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        return await self._repo.get_by_workspace(workspace_id, user_id, skip, limit)


class DeleteConversationUseCase:
    def __init__(self, conversation_repo: ConversationRepository) -> None:
        self._repo = conversation_repo

    async def execute(
        self, conversation_id: UUID, user_id: str
    ) -> None:
        conversation = await self._repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        if conversation.user_id != user_id:
            raise PermissionError("Cannot delete another user's conversation")
        await self._repo.delete(conversation_id)
