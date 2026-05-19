from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from typing import Optional
from app.models.case import Case
from app.models.message import Message
from app.models.document import Document
from app.database import get_db
from app.api.v1.deps import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_cases_stats(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    # Total Cases
    total_cases_stmt = select(func.count(Case.id)).where(Case.user_id == str(current_user.id))
    total_cases_res = await db.execute(total_cases_stmt)
    total_cases = total_cases_res.scalar() or 0

    # Documents Generated
    total_docs_stmt = select(func.count(Document.id)).join(Case).where(Case.user_id == str(current_user.id))
    total_docs_res = await db.execute(total_docs_stmt)
    documents_generated = total_docs_res.scalar() or 0

    # Rights Analysed (legal_brief is not null)
    rights_analysed_stmt = select(func.count(Case.id)).where(
        Case.user_id == str(current_user.id),
        Case.legal_brief.isnot(None)
    )
    rights_analysed_res = await db.execute(rights_analysed_stmt)
    rights_analysed = rights_analysed_res.scalar() or 0

    # Cases Filed (status == "filed")
    cases_filed_stmt = select(func.count(Case.id)).where(
        Case.user_id == str(current_user.id),
        Case.status == "filed"
    )
    cases_filed_res = await db.execute(cases_filed_stmt)
    cases_filed = cases_filed_res.scalar() or 0

    return {
        "total_cases": total_cases,
        "documents_generated": documents_generated,
        "rights_analysed": rights_analysed,
        "cases_filed": cases_filed
    }

@router.get("/activity")
async def get_cases_activity(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    result = await db.execute(
        select(Case)
        .where(Case.user_id == str(current_user.id))
        .order_by(Case.updated_at.desc())
    )
    cases = result.scalars().all()
    
    activity_feed = []
    for c in cases:
        issue_name = c.issue_type.title() if c.issue_type else "Legal"
        
        if c.status == "filed":
            title = f"{issue_name} Petition"
            ref = c.case_ref or "N/A"
            subtitle = f"Filed at court (Ref: {ref})"
            status = "completed"
        elif c.status == "drafting":
            title = f"{issue_name} Draft Review"
            subtitle = "Specialist collecting requirements"
            status = "processing"
        else:
            # 'draft', 'consultation', 'analysed', etc.
            title = f"{issue_name} Analysis"
            subtitle = "Scanning laws and case facts"
            status = "processing"
            
        activity_feed.append({
            "id": f"act_{c.id}",
            "title": title,
            "subtitle": subtitle,
            "status": status,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
        
    return activity_feed

@router.get("/")
async def get_cases(
    limit: Optional[int] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    query = select(Case).where(Case.user_id == str(current_user.id)).order_by(Case.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()
    return {"cases": cases}

@router.get("/{case_id}")
async def get_case(
    case_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.user_id == str(current_user.id)
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404,
                            detail="Case not found")
    return case

@router.get("/{case_id}/messages")
async def get_case_messages(
    case_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    result = await db.execute(
        select(Message)
        .where(Message.case_id == case_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return {"messages": messages}

