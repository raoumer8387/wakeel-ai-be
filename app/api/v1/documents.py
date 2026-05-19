from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.models.document import Document
from app.database import get_db
from app.api.v1.deps import get_current_user
from jose import jwt, JWTError
from app.config import settings

router = APIRouter()

@router.get("/{case_id}")
async def get_case_documents(
    case_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    result = await db.execute(
        select(Document)
        .where(Document.case_id == case_id)
    )
    documents = result.scalars().all()
    return {"documents": documents}

@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    token: str = Query(..., description="JWT access token"),
    db = Depends(get_db)
):
    """Download a PDF document. Accepts JWT token as a query parameter
    so it can be opened directly in a browser/WebView."""
    # Validate token from query param
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(
        select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404,
                            detail="Document not found")
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=f"wakeel_ai_{doc.case_id}.pdf"
    )
