import logging
from app.agent.core.agent import LegalAnalystAgent

# Disable verbose logging for a clean output
logging.basicConfig(level=logging.WARNING)

def run_test():
    agent = LegalAnalystAgent()
    
    print("=" * 50)
    print("      WAKEEL-AI: LEGAL ANALYST AGENT TEST      ")
    print("=" * 50)
    
    # Example complex problem involving multiple laws
    query = "I have been living at my parents' house for six months because of a fight. My husband is not sending any money for our 5-year-old son's school fees or my expenses. What legal steps can I take to get 'Kharcha' (maintenance) without filing for a full divorce yet?"
    
    print(f"\nCITIZEN PROBLEM:\n\"{query}\"")
    print("\nProcessing... (Thinking with Pakistani Law & Amendments)")
    
    brief = agent.process_request(query)
    
    print("\n" + brief)
    print("=" * 50)

if __name__ == "__main__":
    run_test()
