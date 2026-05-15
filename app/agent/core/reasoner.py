from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.agent.core.schemas import LegalBrief

class LawReasoner:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            openai_api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=2000
        )
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are 'Wakeel-AI', a Senior Legal Analyst specialized in Pakistani Family Law.
        Based on the provided legal excerpts, analyze the user's problem and generate a structured legal brief.
        
        RETRIEVED LAWS & AMENDMENTS:
        {context}
        
        USER PROBLEM:
        {query}
        
        INSTRUCTIONS:
        1. Be precise. If an amendment exists (look at the 'year' and 'is_amendment' metadata), prioritize the newer rule.
        2. Classify the problem clearly.
        3. List specific Statutes and Sections.
        4. Provide an 'Impact Analysis' explaining what this means for the citizen.
        5. If the law is silent or requires a lawyer, state that clearly.
        
        LEGAL BRIEF FORMAT:
        ---
        ### 1. Problem Classification
        [Type of legal issue]
        
        ### 2. Relevant Statutes & Sections
        [List laws and specific section numbers]
        
        ### 3. Legal Analysis
        [Step-by-step explanation of the legal position]
        
        ### 4. Impact Analysis & Recommendations
        [What the user should do next]
        ---
        """)

    def analyze(self, query: str, retrieved_docs: List[Dict]) -> str:
        # Format context from docs
        context_blocks = []
        for d in retrieved_docs:
            meta = d['metadata']
            context_blocks.append(
                f"Source: {meta['filename']} ({meta['year']})\n"
                f"Section: {meta['section_number']}\n"
                f"Content: {d['content']}\n"
            )
        
        context = "\n---\n".join(context_blocks)
        
        # Generate analysis
        response = self.llm.invoke(
            self.prompt.format(query=query, context=context)
        )
        
        return response.content

if __name__ == "__main__":
    reasoner = LawReasoner()
    # Test with mock data
    mock_docs = [{"content": "No person shall marry a second wife without permission of Arbitration Council.", "metadata": {"filename": "MFLO 1961", "year": 1961, "section_number": "6"}}]
    print(reasoner.analyze("Can I marry again?", mock_docs))
