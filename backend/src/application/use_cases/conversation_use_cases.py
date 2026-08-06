from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from src.domain.entities.conversation import Conversation, Message, MessageRole, Citation
from src.domain.repositories.conversation_repository import ConversationRepository
from src.domain.services.document_service import DocumentService
# In a real app we'd have an LLMService or RAGService
# from src.domain.services.llm_service import LLMService

class CreateConversationUseCase:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def execute(self, workspace_id: UUID, user_id: UUID, title: str) -> Conversation:
        conversation = Conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title
        )
        return await self.conversation_repository.create(conversation)

class SendMessageUseCase:
    def __init__(
        self, 
        conversation_repository: ConversationRepository,
        document_service: DocumentService
    ):
        self.conversation_repository = conversation_repository
        self.document_service = document_service

    async def execute(
        self, 
        workspace_id: UUID, 
        user_id: UUID,
        query: str, 
        conversation_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Message:
        if not conversation_id:
            # Create a new conversation
            conversation = await CreateConversationUseCase(self.conversation_repository).execute(
                workspace_id, user_id, title=query[:50]
            )
            conversation_id = conversation.id

        # 1. Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=query
        )
        await self.conversation_repository.add_message(user_msg)

        # 2. Search knowledge base
        chunks = await self.document_service.search_documents(workspace_id, query, filters)
        
        # 3. Formulate RAG answer (simulated here)
        # Would use self.llm_service.generate_answer(query, chunks)
        answer_text = f"Simulated answer based on {len(chunks)} sources."
        
        citations = []
        for i, chunk in enumerate(chunks[:3]):
            citations.append(Citation(
                document_id=chunk.document_id,
                document_title=chunk.metadata.get("title", "Unknown"),
                chunk_id=chunk.id,
                content_snippet=chunk.content[:100],
                page_number=chunk.page_number,
                relevance_score=0.9 - (i * 0.1)
            ))

        # 4. Save assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=answer_text,
            sources=citations,
            token_count=150,
            model_used="gpt-4o-mini"
        )
        await self.conversation_repository.add_message(assistant_msg)
        
        return assistant_msg

class GetConversationHistoryUseCase:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def execute(self, conversation_id: UUID) -> List[Message]:
        return await self.conversation_repository.get_messages(conversation_id)

class DeleteConversationUseCase:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def execute(self, conversation_id: UUID) -> bool:
        return await self.conversation_repository.delete(conversation_id)
