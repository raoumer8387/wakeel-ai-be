from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalysisRequest(BaseModel):
    query: str

class LegalSource(BaseModel):
    filename: str
    section_number: str
    title: Optional[str] = None
    year: Optional[int] = None

class AnalysisResponse(BaseModel):
    brief: str
    sources: List[LegalSource]
