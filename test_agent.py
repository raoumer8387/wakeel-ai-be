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
    
    result = agent.analyze(query, f"User: {query}")
    
    print("\nRESPONSE:")
    print(result.get("response", ""))
    print("\nREADY FOR DRAFTING:", result.get("ready_for_drafting"))
    print("\nLEGAL BRIEF:")
    print(result.get("legal_brief"))
    print("=" * 50)

if __name__ == "__main__":
    run_test()
