from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.domain.entities.conversation import Conversation, Message, Citation
from src.domain.repositories.conversation_repository import ConversationRepository
from src.infrastructure.database.models.conversation_model import ConversationModel, MessageModel

class PostgresConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ConversationModel) -> Conversation:
        return Conversation(
            id=model.id,
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            title=model.title,
            total_tokens=model.total_tokens,
            total_cost=model.total_cost,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_msg_entity(self, model: MessageModel) -> Message:
        sources = []
        for s in model.sources:
            if isinstance(s, dict):
                sources.append(Citation(**s))
            
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            sources=sources,
            token_count=model.token_count,
            latency_ms=model.latency_ms,
            model_used=model.model_used,
            cost_usd=model.cost_usd,
            created_at=model.created_at
        )

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        result = await self.session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await self.session.execute(
            select(ConversationModel)
            .where(ConversationModel.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .order_by(ConversationModel.updated_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            workspace_id=conversation.workspace_id,
            user_id=conversation.user_id,
            title=conversation.title,
            total_tokens=conversation.total_tokens,
            total_cost=conversation.total_cost,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, conversation: Conversation) -> Conversation:
        result = await self.session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.title = conversation.title
            model.total_tokens = conversation.total_tokens
            model.total_cost = conversation.total_cost
            await self.session.flush()
            return self._to_entity(model)
        raise ValueError("Conversation not found")

    async def delete(self, conversation_id: UUID) -> bool:
        result = await self.session.execute(
            delete(ConversationModel).where(ConversationModel.id == conversation_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def add_message(self, message: Message) -> Message:
        sources_dict_list = [s.model_dump(mode='json') for s in message.sources]
        
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            sources=sources_dict_list,
            token_count=message.token_count,
            latency_ms=message.latency_ms,
            model_used=message.model_used,
            cost_usd=message.cost_usd,
            created_at=message.created_at
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_msg_entity(model)

    async def get_messages(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        result = await self.session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_msg_entity(m) for m in result.scalars().all()]

    async def get_message_by_id(self, message_id: UUID) -> Optional[Message]:
        result = await self.session.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        model = result.scalar_one_or_none()
        return self._to_msg_entity(model) if model else None
