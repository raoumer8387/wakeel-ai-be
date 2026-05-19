import json
from app.agent.document_specialist import DocumentSpecialistAgent

def run_test():
    print("=" * 60)
    print("   WAKEEL-AI: DOCUMENT SPECIALIST AGENT TEST (AGENT 2)   ")
    print("=" * 60)
    
    agent = DocumentSpecialistAgent()
    
    # Mock Legal Brief as it would come from Agent 1 (Legal Analyst)
    mock_legal_brief = {
        "issue_type": "khula",
        "problem_classification": "Dissolution of Marriage via Khula",
        "relevant_statutes": ["MFLO 1961 Section 8", "Family Courts Act 1964 Section 12"],
        "analysis": "The wife is seeking khula. She is willing to return the Haq Mehr."
    }
    
    # Mock user problem
    user_problem = "I want to get a Khula from my husband. My name is Ayesha Tariq. My husband's name is Ali Raza. We got married on 10th March 2020 in Lahore. My CNIC is 35201-1234567-8 and his is 35201-8765432-1. The Mehr was 50,000 Rs. We separated on 1st January 2026 because of domestic abuse. I live at Johar Town, Lahore. He lives at DHA Phase 1, Lahore."
    
    print(f"\nCITIZEN PROBLEM:\n\"{user_problem}\"")
    print("\nProcessing... (Extracting placeholders, drafting petition, generating PDF)")
    
    result = agent.process(
        legal_brief=mock_legal_brief,
        user_problem=user_problem,
        case_id="CASE_KHULA_TEST"
    )
    
    print("\n" + "=" * 60)
    print("                  PROCESS COMPLETED                   ")
    print("=" * 60)
    
    print(json.dumps(result, indent=2))
    print(f"\nSuccessfully generated PDF at: {result.get('pdf_path')}")

if __name__ == "__main__":
    run_test()
