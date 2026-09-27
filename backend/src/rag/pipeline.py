"""Simple local document indexing and question-answering pipeline."""
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_ollama import ChatOllama
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.core.config import settings


class RagPipeline:
    def __init__(self) -> None:
        self.embeddings = FastEmbedEmbeddings(model_name=settings.embedding_model)
        self._indexed_files: set[str] = set()

    def index(self, paths: list[Path]) -> dict:
        documents: list[Document] = []
        for path in paths:
            documents.extend(self._load(path))
        if not documents:
            return {"files": 0, "chunks": 0}

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = index

        client = QdrantClient(url=settings.qdrant_url)
        if client.collection_exists(settings.qdrant_collection):
            client.delete_collection(settings.qdrant_collection)
        QdrantVectorStore.from_documents(
            chunks,
            self.embeddings,
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
        )
        self._indexed_files = {path.name for path in paths}
        return {"files": len(paths), "chunks": len(chunks)}

    def ask(self, question: str) -> dict:
        vector_store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            collection_name=settings.qdrant_collection,
            url=settings.qdrant_url,
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": settings.retrieval_top_k})
        context = retriever.invoke(question)
        if not context:
            return {"answer": "I could not find that information in the indexed documents.", "sources": []}

        prompt = ChatPromptTemplate.from_template(
            """Answer the question using only the context below. """
            """If the answer is not in the context, say you could not find it.\n\n"
            "Context:\n{context}\n\nQuestion: {question}"""
        )
        chain = prompt | ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0,
        )
        response = chain.invoke({"context": "\n\n".join(doc.page_content for doc in context), "question": question})
        sources = [
            {
                "filename": doc.metadata.get("filename", Path(doc.metadata.get("source", "")).name),
                "chunk_id": doc.metadata.get("chunk_id", 0),
            }
            for doc in context
        ]
        return {"answer": response.content, "sources": sources}

    @staticmethod
    def remove_file(filename: str) -> None:
        client = QdrantClient(url=settings.qdrant_url)
        if client.collection_exists(settings.qdrant_collection):
            client.delete(
                collection_name=settings.qdrant_collection,
                points_selector=Filter(
                    must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
                ),
            )
        self._indexed_files.discard(filename)

    @staticmethod
    def _load(path: Path) -> list[Document]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        elif suffix == ".docx":
            loader = Docx2txtLoader(str(path))
        else:
            loader = TextLoader(str(path), encoding="utf-8")
        documents = loader.load()
        for document in documents:
            document.metadata.update({"filename": path.name, "file_path": str(path), "file_type": suffix[1:]})
        return documents