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

    def analyze(self, latest_message: str, chat_history: str) -> dict:
        logger.info(f"Processing legal request: {latest_message[:50]}...")
        
        # 1. Route to relevant law families
        decision = self.router.route(latest_message)
        logger.info(f"Routed to families: {decision.relevant_families}")
        
        # 2. Retrieve relevant sections
        docs = self.retriever.retrieve(latest_message, decision.relevant_families)
        logger.info(f"Retrieved {len(docs)} legal documents.")
        
        # 3. Reason and generate brief/response
        result = self.reasoner.analyze(chat_history, docs)
        
        return result
