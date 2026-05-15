import logging
import os
import json
from dotenv import load_dotenv
from app.agent.ingest.pdf_parser import PDFParser
from app.agent.ingest.ocr_recovery import OCRRecovery
from app.agent.ingest.amendment_linker import AmendmentLinker
from app.agent.ingest.vectorizer import LawVectorizer
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHECKPOINT_FILE = "ingestion_progress.json"

def load_progress():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"completed_files": []}

def save_progress(filename):
    progress = load_progress()
    if filename not in progress["completed_files"]:
        progress["completed_files"].append(filename)
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(progress, f)

def main():
    load_dotenv()
    progress = load_progress()
    
    logger.info("Starting Ingestion Pipeline...")
    
    # 1. Parse PDFs (Raw Extraction)
    parser = PDFParser(settings.DATA_PATH)
    raw_sections = parser.parse_all()
    
    # Group sections by PDF
    sections_by_pdf = {}
    for s in raw_sections:
        if s.pdf_filename not in sections_by_pdf:
            sections_by_pdf[s.pdf_filename] = []
        sections_by_pdf[s.pdf_filename].append(s)
    
    recovery = OCRRecovery()
    linker = AmendmentLinker()
    vectorizer = LawVectorizer()
    
    # 2. Process each PDF (with checkpoint check)
    for filename, pdf_sections in sections_by_pdf.items():
        if filename in progress["completed_files"]:
            logger.info(f"Skipping already processed file: {filename}")
            continue
            
        logger.info(f"Processing: {filename}...")
        
        # Recover text
        recovered = recovery.recover_pdf_text(pdf_sections)
        
        # Link amendments
        final_sections = linker.link_amendments(recovered)
        
        # Index to ChromaDB
        logger.info(f"Indexing to ChromaDB: {filename}")
        vectorizer.index_sections(final_sections)
        
        # Save progress
        save_progress(filename)
        logger.info(f"Successfully finished: {filename}")
    
    logger.info("Ingestion Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
