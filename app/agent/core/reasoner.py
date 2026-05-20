from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import settings

class LawReasoner:
    def __init__(self):
        from app.agent.core.llm import get_resilient_llm
        self.llm = get_resilient_llm(temperature=0.3, max_tokens=2000)
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are 'Wakeel-AI', a Senior Legal Analyst specialized in Pakistani Family Law.
        You are having a 2-way conversation with a user about a legal issue.
        
        RETRIEVED LAWS & AMENDMENTS (if any):
        {context}
        
        CONVERSATION HISTORY:
        {chat_history}
        
        INSTRUCTIONS:
        1. CAREFULLY READ the entire CONVERSATION HISTORY above. The user may have already provided important details like their name, spouse's name, address, CNIC, dates, etc. NEVER ask for information the user has ALREADY provided in the conversation.
        2. If the user's problem is still vague even after reviewing the history, ask clarifying questions — but ONLY about things NOT yet mentioned.
        3. If the user has provided enough detail to understand their core legal issue (e.g. they want a divorce, maintenance, custody), provide a "Final Analysis and Recommendations" using the retrieved laws.
        4. At the very end of your "Final Analysis and Recommendations", ask the user exactly: "Would you like me to prepare a draft [Type of Petition] for you?"
        5. ALWAYS respond in the SAME LANGUAGE and SCRIPT as the user.
        
        You MUST return ONLY a valid JSON object with the following structure:
        {{
            "response": "Your conversational reply to the user (this is what the user sees). Include your clarifying questions OR your Final Analysis here.",
            "ready_for_drafting": true, // Set to true ONLY IF you have provided the Final Analysis AND asked if they want a draft. Otherwise false.
            "legal_brief": {{ // If ready_for_drafting is true, populate this. Otherwise, set to null.
                "issue_type": "khula|talaq|maintenance|custody|dissolution|dowry|parents_rights",
                "issue_summary": "Brief summary",
                "relevant_laws": ["law 1", "law 2"],
                "rights": ["right 1"],
                "jurisdiction": "City",
                "confidence_score": 0.9
            }}
        }}
        """)

    def analyze(self, chat_history: str, retrieved_docs: List[Dict]) -> dict:
        context_blocks = []
        for d in retrieved_docs:
            meta = d['metadata']
            context_blocks.append(
                f"Source: {meta['filename']} ({meta['year']})\n"
                f"Section: {meta['section_number']}\n"
                f"Content: {d['content']}\n"
            )
        
        context = "\n---\n".join(context_blocks)
        
        chain = self.prompt | self.llm | self.parser
        return chain.invoke({"chat_history": chat_history, "context": context})
