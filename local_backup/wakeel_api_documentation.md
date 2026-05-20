# Wakeel-AI API Documentation

This document outlines the REST API endpoints and Server-Sent Event (SSE) streams built for the Wakeel-AI backend orchestration layer. All endpoints require authentication via a JWT token passed in the `Authorization: Bearer <token>` header.

---

## 1. Chat & Orchestration

### `POST /api/v1/chat/query`
The primary entry point for interacting with the AI Legal Analyst and Document Specialist pipeline. It streams responses back to the client using Server-Sent Events (SSE).

**Request Body (`application/json`)**:
```json
{
  "message": "I want a Khula. I live in Lahore.",
  "case_id": "CASE_A1B2C3D4" // Optional. If omitted, a new case is generated.
}
```

**Response (`text/event-stream`)**:
Streams a series of events as the pipeline progresses. Each chunk is formatted as `data: {"event": "...", "message": "...", "data": {...}}`.

*Possible Events:*
- `pipeline_start`: Indicates the backend has received the request.
- `agent1_start` / `agent1_done`: Progression of the Legal Analyst agent. `agent1_done` includes the generated legal brief in the `data` payload.
- `agent2_start` / `agent2_question`: If the Document Specialist detects missing fields, it emits `agent2_question` with a string asking the user for details. The stream **closes** after this, awaiting the user to send a new `POST` request with their answer.
- `agent2_done`: Indicates the PDF has been successfully drafted.
- `simulation_start` / `simulation_done`: Indicates the mock filing to the family court has completed.
- `complete`: Final event indicating the entire flow is finished.
- `error`: Emitted if an exception occurs during the pipeline.

---

## 2. Cases Management

### `GET /api/v1/cases/`
Retrieves a list of all cases belonging to the currently authenticated user, ordered by creation date (newest first).

**Response (`application/json`)**:
```json
{
  "cases": [
    {
      "id": "CASE_A1B2C3D4",
      "user_id": "user-uuid",
      "title": "Khula Petition — Wife Divorce",
      "issue_type": "khula",
      "status": "filed", // 'draft', 'analysed', or 'filed'
      "legal_brief": { ... },
      "action_log": [ ... ],
      "case_ref": "FC-LHR-2024-1234",
      "created_at": "2024-05-17T12:00:00Z",
      "updated_at": "2024-05-17T12:05:00Z"
    }
  ]
}
```

### `GET /api/v1/cases/{case_id}`
Retrieves the details of a specific case.

**Response (`application/json`)**:
Returns the single `Case` object as shown in the list above. Returns `404 Not Found` if the case does not exist or doesn't belong to the user.

### `GET /api/v1/cases/{case_id}/messages`
Retrieves the entire chronological chat history for a specific case.

**Response (`application/json`)**:
```json
{
  "messages": [
    {
      "id": "msg-uuid-1",
      "case_id": "CASE_A1B2C3D4",
      "role": "user",
      "content": "I want a Khula.",
      "metadata_": null,
      "created_at": "2024-05-17T12:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "case_id": "CASE_A1B2C3D4",
      "role": "agent2",
      "content": "Okay, could you provide your CNIC?",
      "metadata_": { "missing_fields": ["APPLICANT_CNIC"] },
      "created_at": "2024-05-17T12:00:10Z"
    }
  ]
}
```

---

## 3. Documents Management

### `GET /api/v1/documents/{case_id}`
Retrieves a list of all documents generated for a specific case.

**Response (`application/json`)**:
```json
{
  "documents": [
    {
      "id": "doc-uuid",
      "case_id": "CASE_A1B2C3D4",
      "type": "khula",
      "file_path": "data/output/CASE_A1B2C3D4_khula.pdf",
      "generated_by": "document_specialist_agent",
      "created_at": "2024-05-17T12:05:00Z"
    }
  ]
}
```

### `GET /api/v1/documents/{doc_id}/download`
Downloads the actual PDF file for a specific document ID.

**Response**:
Returns the raw binary file as a `FileResponse` with `Content-Type: application/pdf`.
If the document is not found in the DB, returns `404 Not Found`.
