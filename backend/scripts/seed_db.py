"""Seed the database with demo data for development."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from uuid import uuid4
from src.infrastructure.database.connection import AsyncSessionLocal, create_tables
from src.infrastructure.database.models.workspace_model import WorkspaceModel, WorkspaceMemberModel
from src.infrastructure.database.models.document_model import DocumentModel
from src.infrastructure.database.models.conversation_model import ConversationModel, MessageModel


async def seed() -> None:
    print("Creating tables...")
    await create_tables()
    
    async with AsyncSessionLocal() as session:
        # Demo workspace
        workspace_id = uuid4()
        workspace = WorkspaceModel(
            id=workspace_id,
            name="Acme Corporation",
            slug="acme-corp",
            owner_id="user_demo_001",
            plan="PROFESSIONAL",
            settings_={
                "model_preference": "qwen2.5:7b",
                "max_tokens_per_request": 8000,
                "auto_evaluate": True,
            },
            document_count=3,
            total_tokens_used=125_400,
            monthly_cost_usd=2.50,
        )
        session.add(workspace)
        
        # Demo member
        member = WorkspaceMemberModel(
            workspace_id=workspace_id,
            user_id="user_demo_001",
            role="OWNER",
        )
        session.add(member)
        
        # Demo documents
        docs = [
            DocumentModel(
                id=uuid4(),
                workspace_id=workspace_id,
                user_id="user_demo_001",
                title="Q3 2024 Financial Report",
                file_name="q3_financial_report.pdf",
                file_path="./uploads/q3_financial_report.pdf",
                file_size=2_048_000,
                document_type="PDF",
                status="READY",
                total_chunks=45,
                metadata_={"pages": 28, "author": "Finance Team"},
            ),
            DocumentModel(
                id=uuid4(),
                workspace_id=workspace_id,
                user_id="user_demo_001",
                title="Employee Handbook 2024",
                file_name="employee_handbook.docx",
                file_path="./uploads/employee_handbook.docx",
                file_size=512_000,
                document_type="DOCX",
                status="READY",
                total_chunks=22,
                metadata_={"pages": 54, "department": "HR"},
            ),
            DocumentModel(
                id=uuid4(),
                workspace_id=workspace_id,
                user_id="user_demo_001",
                title="Product Roadmap 2025",
                file_name="roadmap_2025.md",
                file_path="./uploads/roadmap_2025.md",
                file_size=64_000,
                document_type="MARKDOWN",
                status="PROCESSING",
                total_chunks=0,
                metadata_={},
            ),
        ]
        for doc in docs:
            session.add(doc)
        
        # Demo conversation
        conv_id = uuid4()
        conv = ConversationModel(
            id=conv_id,
            workspace_id=workspace_id,
            user_id="user_demo_001",
            title="Q3 Revenue Analysis",
            total_tokens=1_240,
            total_cost=0.002,
        )
        session.add(conv)
        
        # Demo messages
        messages = [
            MessageModel(
                id=uuid4(),
                conversation_id=conv_id,
                role="USER",
                content="What was our total revenue in Q3 2024?",
                sources=[],
                token_count=12,
            ),
            MessageModel(
                id=uuid4(),
                conversation_id=conv_id,
                role="ASSISTANT",
                content="Based on the Q3 2024 Financial Report, Acme Corporation achieved **total revenue of $12.4M** in Q3 2024, representing a **23% year-over-year increase**. Key drivers included:\n\n- Product sales: $8.2M (+18%)\n- Services: $3.1M (+31%)\n- Licensing: $1.1M (+28%)",
                sources=[
                    {
                        "document_id": str(docs[0].id),
                        "document_title": "Q3 2024 Financial Report",
                        "chunk_id": str(uuid4()),
                        "content_snippet": "Total revenue for Q3 2024 was $12.4 million, a 23% increase year-over-year...",
                        "page_number": 4,
                        "relevance_score": 0.94,
                    }
                ],
                token_count=120,
                latency_ms=1843,
                model_used="qwen2.5:7b",
                cost_usd=0.002,
            ),
        ]
        for msg in messages:
            session.add(msg)
        
        await session.commit()
        print(f"✅ Seeded demo data:")
        print(f"   - Workspace: 'Acme Corporation' (ID: {workspace_id})")
        print(f"   - 3 documents (2 READY, 1 PROCESSING)")
        print(f"   - 1 conversation with 2 messages")
        print(f"\nYou can now start the backend and explore the API at http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
