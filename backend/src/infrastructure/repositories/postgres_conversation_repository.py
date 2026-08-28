"""PostgreSQL implementation of ConversationRepository."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from src.domain.entities.conversation import Conversation, Message, MessageRole, Citation
from src.domain.repositories.conversation_repository import ConversationRepository
from src.infrastructure.database.models.conversation_model import ConversationModel, MessageModel

logger = logging.getLogger(__name__)


class PostgresConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _message_to_entity(m: MessageModel) -> Message:
        sources = [
            Citation(
                document_id=UUID(s["document_id"]) if s.get("document_id") else UUID(int=0),
                document_title=s.get("document_title", ""),
                chunk_id=UUID(s["chunk_id"]) if s.get("chunk_id") else UUID(int=0),
                content_snippet=s.get("content_snippet", ""),
                page_number=s.get("page_number"),
                relevance_score=s.get("relevance_score", 0.0),
            )
            for s in (m.sources or [])
        ]
        return Message(
            id=m.id,
            conversation_id=m.conversation_id,
            role=MessageRole(m.role),
            content=m.content,
            sources=sources,
            token_count=m.token_count,
            latency_ms=m.latency_ms,
            model_used=m.model_used,
            cost_usd=float(m.cost_usd) if m.cost_usd else None,
            created_at=m.created_at,
        )

    @staticmethod
    def _conv_to_entity(c: ConversationModel, messages: list[Message] | None = None) -> Conversation:
        return Conversation(
            id=c.id,
            workspace_id=c.workspace_id,
            user_id=c.user_id,
            title=c.title,
            messages=messages or [],
            total_tokens=c.total_tokens or 0,
            total_cost=float(c.total_cost) if c.total_cost else 0.0,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        messages = await self.get_messages(conversation_id)
        return self._conv_to_entity(model, messages)

    async def get_by_workspace(
        self, workspace_id: UUID, user_id: str, skip: int = 0, limit: int = 20
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(ConversationModel)
            .where(
                ConversationModel.workspace_id == workspace_id,
                ConversationModel.user_id == user_id,
            )
            .order_by(ConversationModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._conv_to_entity(m) for m in result.scalars().all()]

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            workspace_id=conversation.workspace_id,
            user_id=conversation.user_id,
            title=conversation.title,
            total_tokens=conversation.total_tokens,
            total_cost=conversation.total_cost,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._conv_to_entity(model)

    async def update(self, conversation: Conversation) -> Conversation:
        await self._session.execute(
            update(ConversationModel)
            .where(ConversationModel.id == conversation.id)
            .values(
                title=conversation.title,
                total_tokens=conversation.total_tokens,
                total_cost=conversation.total_cost,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        return await self.get_by_id(conversation.id)

    async def delete(self, conversation_id: UUID) -> bool:
        result = await self._session.execute(
            delete(ConversationModel).where(ConversationModel.id == conversation_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def add_message(self, message: Message) -> Message:
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role.value,
            content=message.content,
            sources=[{
                "document_id": str(c.document_id),
                "document_title": c.document_title,
                "chunk_id": str(c.chunk_id),
                "content_snippet": c.content_snippet,
                "page_number": c.page_number,
                "relevance_score": c.relevance_score,
            } for c in message.sources],
            token_count=message.token_count,
            latency_ms=message.latency_ms,
            model_used=message.model_used,
            cost_usd=message.cost_usd,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        
        # Update conversation totals
        await self._session.execute(
            update(ConversationModel)
            .where(ConversationModel.id == message.conversation_id)
            .values(
                total_tokens=ConversationModel.total_tokens + (message.token_count or 0),
                total_cost=ConversationModel.total_cost + (message.cost_usd or 0),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        return self._message_to_entity(model)

    async def get_messages(
        self, conversation_id: UUID, limit: int = 50
    ) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at)
            .limit(limit)
        )
        return [self._message_to_entity(m) for m in result.scalars().all()]

    async def get_message_by_id(self, message_id: UUID) -> Optional[Message]:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        model = result.scalar_one_or_none()
        return self._message_to_entity(model) if model else None
