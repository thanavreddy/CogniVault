# API Reference

## Authentication
All API endpoints require a Bearer token in the `Authorization` header provided by Clerk.

## Documents API

### `POST /api/v1/workspaces/{workspace_id}/documents`
Uploads a document to a workspace.
**Request:**
- `Content-Type: multipart/form-data`
- `file`: (binary)
**Response:**
```json
{
  "id": "uuid",
  "title": "Document Title",
  "status": "processing"
}
```

### `GET /api/v1/workspaces/{workspace_id}/documents`
Lists documents in a workspace.

## Conversations API

### `POST /api/v1/workspaces/{workspace_id}/conversations`
Creates a new conversation thread.
**Request:**
```json
{
  "title": "New Chat"
}
```

### `POST /api/v1/conversations/{conversation_id}/messages`
Sends a message to the AI.
**Request:**
```json
{
  "content": "What is our Q3 revenue?",
  "role": "user"
}
```
**Response:**
```json
{
  "id": "msg_uuid",
  "content": "The Q3 revenue was $5M.",
  "sources": [{"doc_id": "uuid", "snippet": "..."}],
  "role": "assistant"
}
```

## Workspaces API
### `GET /api/v1/workspaces`
Lists workspaces for the current user.

## Analytics API
### `GET /api/v1/analytics/usage`
Returns token usage and cost metrics.

## Health API
### `GET /health`
Returns system health status.
