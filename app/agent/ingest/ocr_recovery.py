import re
import logging
import time
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agent.core.schemas import ParsedSection, LawFamily
from app.config import settings

logger = logging.getLogger(__name__)

class OCRRecovery:
    def __init__(self):
        # Initialize OpenRouter LLM (Using 3B Free for stability)
        if settings.OPENROUTER_API_KEY:
            print(f"DEBUG: Using OpenRouter Key ending in: ...{settings.OPENROUTER_API_KEY[-4:]}")
            self.llm = ChatOpenAI(
                model="google/gemini-2.0-flash-001",
                openai_api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                max_tokens=2000,
                default_headers={
                    "HTTP-Referer": "https://wakeel.ai",
                    "X-Title": "Wakeel AI Legal Agent",
                }
            )
            
            self.prompt = ChatPromptTemplate.from_template("""
            You are a Legal Data Recovery Expert specializing in Pakistani Gazette documents.
            The following text is from an old law PDF. It has many OCR errors (e.g., 'iho' instead of 'the').
            
            TASK:
            1. Clean the text and fix typos.
            2. Extract individual Sections or Articles.
            3. Return a JSON list of objects: [[{{"section_number": "...", "title": "...", "body": "..."}}]]
            
            NOISY TEXT:
            {noisy_text}
            
            JSON OUTPUT ONLY:
            """)
            
            self.chain = self.prompt | self.llm | JsonOutputParser()
        else:
            self.llm = None
            logger.warning("OPENROUTER_API_KEY not found. Falling back to local cleaning only.")

        self.common_fixes = {
            r"\biho\b": "the",
            r"\baecree\b": "decree",
            r"\bia\b": "a",
            r"\bFest Pakistan\b": "West Pakistan",
            r"\bF amily\b": "Family",
            r"\bOh ese\b": "Of the",
            r"\bce degnra\b": "decree",
        }

    def clean_text_locally(self, text: str) -> str:
        cleaned = text
        for pattern, replacement in self.common_fixes.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned

    def recover_pdf_text(self, raw_sections: List[ParsedSection]) -> List[ParsedSection]:
        if not raw_sections:
            return []
        
        pdf_filename = raw_sections[0].pdf_filename
        family = raw_sections[0].law_family
        year = raw_sections[0].year
        is_amendment = raw_sections[0].is_amendment
        
        # Combined text for cleaning
        noisy_text = "\n".join([s.body for s in raw_sections])
        
        # ALWAYS do local cleaning first to help the LLM or as fallback
        cleaned_locally = self.clean_text_locally(noisy_text)
        
        # If we have OpenRouter, try to use LLM for better recovery
        if self.llm:
            logger.info(f"Using OpenRouter to recover: {pdf_filename}")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cleaned_data = self.chain.invoke({"noisy_text": cleaned_locally[:15000]}) # Limit tokens
                    
                    recovered_sections = []
                    for item in cleaned_data:
                        # Ensure we always have strings to satisfy Pydantic
                        recovered_sections.append(ParsedSection(
                            law_family=family,
                            pdf_filename=pdf_filename,
                            section_number=str(item.get("section_number") or "Unknown"),
                            title=item.get("title") or "Untitled",
                            body=str(item.get("body") or ""),
                            page_number=1,
                            is_amendment=is_amendment,
                            year=year
                        ))
                    time.sleep(2) # Slight delay
                    return recovered_sections
                except Exception as e:
                    logger.warning(f"OpenRouter attempt {attempt+1} failed: {e}")
                    if "429" in str(e):
                        logger.info("Rate limit hit. Waiting 30 seconds...")
                        time.sleep(30)
                    else:
                        time.sleep(5)
            
            # Fallback to local heuristic if all retries fail
            # (Wait 10s before fallback to be safe)
            time.sleep(10)
            
        # Fallback to local heuristic splitting if LLM fails or is missing
        logger.info(f"Falling back to local heuristic for {pdf_filename}")
        section_pattern = r"(?i)(Section|Article)\s+(\d+[-]?\w*)"
        matches = list(re.finditer(section_pattern, cleaned_locally))
        
        recovered_sections = []
        if not matches:
            recovered_sections.append(ParsedSection(
                law_family=family, pdf_filename=pdf_filename, section_number="Full",
                body=cleaned_locally, page_number=1, is_amendment=is_amendment, year=year
            ))
        else:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(cleaned_locally)
                recovered_sections.append(ParsedSection(
                    law_family=family, pdf_filename=pdf_filename,
                    section_number=match.group(0), body=cleaned_locally[start:end].strip(),
                    page_number=1, is_amendment=is_amendment, year=year
                ))
        
        return recovered_sections
