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
    query = "Meri biwi ne khula manga hai, main kya karun?"
    
    print(f"\nCITIZEN PROBLEM:\n\"{query}\"")
    print("\nProcessing... (Thinking with Pakistani Law & Amendments)")
    
    brief, sources = agent.process_request(query)
    
    print("\n" + brief)
    print("\n" + "=" * 50)
    print("      SOURCES RETRIEVED (Verification)      ")
    for s in sources:
        print(f"- {s['metadata']['filename']} | Section: {s['metadata']['section_number']}")
    print("=" * 50)

if __name__ == "__main__":
    run_test()
