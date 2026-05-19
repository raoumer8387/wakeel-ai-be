from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json, uuid
from app.agent.orchestrator import WakeelOrchestrator
from app.models.case import Case
from app.models.message import Message
from app.database import get_db
from app.api.v1.deps import get_current_user

router = APIRouter()
orchestrator = WakeelOrchestrator()

class ChatQueryRequest(BaseModel):
    message: str
    case_id: Optional[str] = None


@router.post("/new")
async def start_new_chat(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Start a brand new chat/case and return the case_id."""
    case_id = f"CASE_{uuid.uuid4().hex[:8].upper()}"
    new_case = Case(
        id=case_id,
        user_id=str(current_user.id),
        status="draft"
    )
    db.add(new_case)
    await db.commit()
    return {"case_id": case_id, "status": "draft"}

@router.post("/query")
async def chat_query(
    body: ChatQueryRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    # Generate case_id if new conversation
    case_id = body.case_id or \
              f"CASE_{uuid.uuid4().hex[:8].upper()}"

    # Create case in DB if new
    if not body.case_id:
        new_case = Case(
            id=case_id,
            user_id=str(current_user.id),
            status="draft"
        )
        db.add(new_case)
        await db.commit()

    # Save user message
    user_msg = Message(
        case_id=case_id,
        role="user",
        content=body.message
    )
    db.add(user_msg)
    await db.commit()

    async def event_stream():
        try:
            async for event in orchestrator.run_pipeline(
                user_input=body.message,
                user_id=str(current_user.id),
                case_id=case_id,
                db=db
            ):
                yield f"data: {json.dumps(event)}\n\n"
            yield f"data: {json.dumps({'event': 'stream_end'})}\n\n"
        except Exception as e:
            error_event = {
                "event": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Connection": "keep-alive"
        }
    )
