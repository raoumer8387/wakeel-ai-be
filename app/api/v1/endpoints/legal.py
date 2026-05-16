from fastapi import APIRouter, HTTPException, Depends
from app.agent.core.agent import LegalAnalystAgent
from app.agent.core.api_schemas import AnalysisRequest, AnalysisResponse, LegalSource
from typing import List

router = APIRouter()

# Initialize the agent once when the module loads
agent = LegalAnalystAgent()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_legal_problem(request: AnalysisRequest):
    """
    Analyzes a citizen's legal problem and returns a professional brief 
    grounded in Pakistani Family Law.
    """
    try:
        brief, docs = agent.process_request(request.query)
        
        # Format sources for the API
        sources = []
        for d in docs:
            sources.append(LegalSource(
                filename=d['metadata'].get('filename', 'Unknown'),
                section_number=d['metadata'].get('section_number', 'Unknown'),
                title=d['metadata'].get('title'),
                year=d['metadata'].get('year')
            ))
            
        return AnalysisResponse(
            brief=brief,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legal Agent Error: {str(e)}")
