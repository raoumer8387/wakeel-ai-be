import logging
from app.agent.core.router import LawRouter
from app.agent.core.retriever import LawRetriever
from app.agent.core.reasoner import LawReasoner

logger = logging.getLogger(__name__)

class LegalAnalystAgent:
    def __init__(self):
        self.router = LawRouter()
        self.retriever = LawRetriever()
        self.reasoner = LawReasoner()

    def process_request(self, user_query: str) -> tuple[str, list]:
        logger.info(f"Processing legal request: {user_query[:50]}...")
        
        # 1. Route to relevant law families
        decision = self.router.route(user_query)
        logger.info(f"Routed to families: {decision.relevant_families}")
        
        # 2. Retrieve relevant sections
        docs = self.retriever.retrieve(user_query, decision.relevant_families)
        logger.info(f"Retrieved {len(docs)} legal documents.")
        
        # 3. Reason and generate brief
        brief = self.reasoner.analyze(user_query, docs)
        
        return brief, docs

if __name__ == "__main__":
    # Quick test
    agent = LegalAnalystAgent()
    problem = "I am 16 years old and my parents are forcing me to marry a 40 year old man. What can I do?"
    print("\n--- GENERATED LEGAL BRIEF ---")
    print(agent.process_request(problem))
