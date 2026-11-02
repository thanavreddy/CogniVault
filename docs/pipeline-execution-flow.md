# CogniVault Pipeline Execution Flow

CogniVault is a local-first retrieval-augmented generation (RAG) application.
The frontend sends requests to FastAPI. FastAPI delegates document work and
question answering to `RagPipeline`.

## System Flow

```text
Browser
  |
  | HTTP requests
  v
Next.js API client
  |
  v
FastAPI routers
  |
  +--> DocumentManager --> data/documents
  |
  +--> RagPipeline
          |
          +--> Document loaders --> chunks --> FastEmbed --> Qdrant
          |
          +--> question --> Qdrant retrieval --> prompt --> Ollama
```

## 1. Application Startup

FastAPI creates the application and registers the document and chat routers.
This makes the document endpoints available under `/documents` and the chat
endpoint available under `/chat`.

```python
app = FastAPI(
    title="CogniVault",
    description="A local-first document question-answering API.",
    version="1.0.0",
)
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
```

The frontend API client uses the local FastAPI server by default.

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

## 2. Upload a Document

The user selects a file on the Documents screen and submits it. The frontend
creates a multipart request and sends it to `/documents/upload`.

```typescript
upload: (file: File) => {
  const body = new FormData();
  body.append("file", file);
  return request<Document>("/documents/upload", { method: "POST", body });
}
```

The router passes the uploaded file to `DocumentManager.save`.

```python
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict:
    try:
        return await DocumentManager().save(file)
```

`DocumentManager.save` checks the filename and size, then writes the original
file to the configured documents directory. The original file is not stored in
Qdrant at this point.

```python
filename = Path(upload.filename or "").name
path = self._path_for(filename)
if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
    raise ValueError("Supported file types: PDF, DOCX, TXT, and Markdown")
contents = await upload.read()
path.write_bytes(contents)
return self._metadata(path)
```

## 3. Start Indexing

The user can index all documents or request indexing for a named document. The
frontend sends a `POST` request to `/documents/index`.

```typescript
index: async (filename?: string) => request<{ files: number; chunks: number }>(
  `/documents/index${filename ? `?filename=${encodeURIComponent(filename)}` : ""}`,
  { method: "POST" },
),
```

The router obtains document paths and starts the RAG indexing operation.

```python
@router.post("/index")
def index_documents(filename: str | None = Query(default=None)) -> dict:
    manager = DocumentManager()
    try:
        if filename:
            manager.paths(filename)
        result = RagPipeline().index(manager.paths())
    return {"message": "Documents indexed", **result}
```

In the current implementation, `filename` is checked when supplied, but the
following call uses `manager.paths()` without the filename. Therefore the
index operation rebuilds the index from all stored documents.

## 4. Load Source Documents

`RagPipeline.index` loads each document path. The loader is selected from the
file extension.

```python
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
```

Each loaded document receives metadata used later for source reporting and
Qdrant filtering.

```python
for document in documents:
    document.metadata.update({"filename": path.name, "file_path": str(path), "file_type": suffix[1:]})
return documents
```

## 5. Split Documents into Chunks

The loaded documents are split into overlapping chunks. The chunk size and
overlap come from application settings.

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)
chunks = splitter.split_documents(documents)
for index, chunk in enumerate(chunks):
    chunk.metadata["chunk_id"] = index
```

The default settings are 1,000 characters per chunk and 200 characters of
overlap.

```python
chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")
```

## 6. Create Embeddings and Store Chunks in Qdrant

`RagPipeline` creates the FastEmbed embedding provider when it is constructed.

```python
def __init__(self) -> None:
    self.embeddings = FastEmbedEmbeddings(model_name=settings.embedding_model)
    self._indexed_files: set[str] = set()
```

Before storing the new index, the existing Qdrant collection is deleted when
it already exists. The chunks are then embedded and written to Qdrant.

```python
client = QdrantClient(url=settings.qdrant_url)
if client.collection_exists(settings.qdrant_collection):
    client.delete_collection(settings.qdrant_collection)
QdrantVectorStore.from_documents(
    chunks,
    self.embeddings,
    url=settings.qdrant_url,
    collection_name=settings.qdrant_collection,
)
```

The indexing response reports how many files and chunks were processed.

```python
self._indexed_files = {path.name for path in paths}
return {"files": len(paths), "chunks": len(chunks)}
```

## 7. Submit a Chat Question

The Chat screen sends the trimmed question as JSON to `/chat`.

```typescript
chat: (question: string) => request<ChatResponse>("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question }),
}),
```

FastAPI validates that the question is not empty and passes it to
`RagPipeline.ask`.

```python
class ChatRequest(BaseModel):
    question: str = Field(min_length=1)

@router.post("")
def chat(request: ChatRequest) -> dict:
    try:
        return RagPipeline().ask(request.question)
```

## 8. Retrieve Relevant Chunks

The chat pipeline opens the existing Qdrant collection using the same embedding
model, creates a retriever, and asks it for the configured number of relevant
chunks.

```python
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=self.embeddings,
    collection_name=settings.qdrant_collection,
    url=settings.qdrant_url,
)
retriever = vector_store.as_retriever(search_kwargs={"k": settings.retrieval_top_k})
context = retriever.invoke(question)
```

If retrieval returns no context, the pipeline returns a fallback answer without
calling Ollama.

```python
if not context:
    return {"answer": "I could not find that information in the indexed documents.", "sources": []}
```

## 9. Generate the Answer with Ollama

When context is available, the pipeline creates a prompt that instructs the
model to answer only from the retrieved context.

```python
prompt = ChatPromptTemplate.from_template(
    """Answer the question using only the context below. """
    """If the answer is not in the context, say you could not find it.\n\n"
    "Context:\n{context}\n\nQuestion: {question}"""
)
```

The prompt is chained to the configured local Ollama model and invoked with the
retrieved chunk text and the user's question.

```python
chain = prompt | ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model,
    temperature=0,
)
response = chain.invoke({"context": "\n\n".join(doc.page_content for doc in context), "question": question})
```

## 10. Return the Answer and Sources

The response includes the generated answer and the filename and chunk ID for
each retrieved document chunk.

```python
sources = [
    {
        "filename": doc.metadata.get("filename", Path(doc.metadata.get("source", "")).name),
        "chunk_id": doc.metadata.get("chunk_id", 0),
    }
    for doc in context
]
return {"answer": response.content, "sources": sources}
```

The frontend adds the answer to the conversation and displays the returned
sources below it.

```typescript
const response = await api.chat(current);
setMessages((items) => [...items, {
  role: "assistant",
  content: response.answer,
  sources: response.sources,
}]);
```

## 11. Delete a Document

Deletion removes the source file and then removes matching points from the
Qdrant collection.

```python
manager.delete(filename)
RagPipeline().remove_file(filename)
```

The Qdrant delete uses the stored `filename` metadata to select the document's
points.

```python
client.delete(
    collection_name=settings.qdrant_collection,
    points_selector=Filter(
        must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
    ),
)
```

## External Services Used

The pipeline depends on these configured local services and components:

- FastAPI for the HTTP API.
- The local filesystem for original documents.
- FastEmbed for embeddings.
- Qdrant at `settings.qdrant_url` for vector storage and retrieval.
- Ollama at `settings.ollama_base_url` for answer generation.