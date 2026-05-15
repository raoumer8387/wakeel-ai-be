from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class LawFamily(str, Enum):
    DOWRY_ACT = "dowry_and_bridal_gifts"
    CHILD_MARRIAGE = "child_marriage_restraint"
    DISSOLUTION = "dissolution_muslim_marriages"
    MUSLIM_FAMILY_LAWS = "muslim_family_laws"
    PARENT_PROTECTION = "protection_of_parents"
    FAMILY_COURTS = "family_courts"

class ParsedSection(BaseModel):
    law_family: LawFamily
    pdf_filename: str
    section_number: str = Field(..., description="e.g., 'Section 3' or 'Section 10-A'")
    title: Optional[str] = None
    body: str
    page_number: int
    is_amendment: bool = False
    year: int

class AmendmentMetadata(BaseModel):
    ordinance_number: Optional[str] = None
    year: int
    modifies_section: str
    modification_type: str = Field(..., description="substituted | inserted | omitted")

class ProblemClassification(BaseModel):
    category: str
    sub_category: str
    severity: str
    jurisdiction: str

class StatuteReference(BaseModel):
    law_name: str
    section: str
    text_excerpt: str
    is_amended: bool
    amended_by: Optional[str] = None
    current_status: str

class ImpactAnalysis(BaseModel):
    citizen_rights: str
    potential_penalties: str
    recommended_actions: List[str]
    time_limitations: Optional[str] = None

class LegalBrief(BaseModel):
    problem_classification: ProblemClassification
    relevant_statutes: List[StatuteReference]
    impact_analysis: ImpactAnalysis
    confidence_score: float
    sources_used: List[str]
