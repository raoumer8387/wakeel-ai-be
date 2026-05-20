from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import settings
from app.agent.core.schemas import LawFamily

class RoutingDecision(BaseModel):
    relevant_families: List[str] = Field(description="List of law family names relevant to the query")
    reasoning: str = Field(description="Brief explanation of why these families were chosen")

class LawRouter:
    def __init__(self):
        from app.agent.core.llm import get_resilient_llm
        self.llm = get_resilient_llm(temperature=0, max_tokens=500)
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are a Pakistani Legal Intake Specialist.
        Identify which law families are relevant to the user's problem.
        
        AVAILABLE LAW FAMILIES:
        - muslim_family_laws: General family matters, registration, polygamy.
        - child_marriage_restraint: Issues involving marriage of minors.
        - family_courts: Procedural issues, court jurisdiction, speed of trial.
        - protection_of_parents: Rights of parents against eviction by children.
        - dowry_and_bridal_gifts: Restrictions on dowry, recovery of bridal gifts.
        - dissolution_muslim_marriages: Grounds for divorce (Khula, Cruelty, etc.).
        
        USER PROBLEM:
        {query}
        
        RETURN JSON ONLY:
        {{
            "relevant_families": ["family_name1", "family_name2"],
            "reasoning": "..."
        }}
        """)
        
        self.chain = self.prompt | self.llm | JsonOutputParser()

    def route(self, query: str) -> RoutingDecision:
        try:
            result = self.chain.invoke({"query": query})
            return RoutingDecision(**result)
        except Exception as e:
            # Fallback: Search all families if routing fails
            return RoutingDecision(
                relevant_families=["muslim_family_laws", "family_courts", "dissolution_muslim_marriages"],
                reasoning=f"Routing failed, falling back to default search. Error: {e}"
            )

if __name__ == "__main__":
    router = LawRouter()
    decision = router.route("My husband has married a second wife without my permission.")
    print(decision)
