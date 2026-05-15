import chromadb
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings
from typing import List
import os
import logging
import time

logger = logging.getLogger(__name__)

class LawVectorizer:
    def __init__(self):
        # Local persist directory
        print(f"DEBUG: Vectorizer using path: {settings.CHROMA_PERSIST_DIR}")
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Using Gemini Cloud Embeddings
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            import os
            api_key = os.getenv("GEMINI_API_KEY")

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )
        
        # We no longer delete the collection here to allow for resuming ingestion
        self.collection = self.client.get_or_create_collection(
            name="pakistan_family_laws"
        )
        print(f"DEBUG: Collection '{self.collection.name}' has {self.collection.count()} sections.")

    def index_sections(self, sections: List["ParsedSection"]):
        ids = []
        documents = []
        metadatas = []
        
        chunk_idx = 0
        for section in sections:
            # Split section body into smaller chunks if it's too large
            # (Basic splitting for now)
            chunks = [section.body[i:i+2000] for i in range(0, len(section.body), 2000)]
            
            for i, chunk in enumerate(chunks):
                # CREATE UNIQUE ID: LawFamily_Filename_Section_ChunkIndex_Timestamp
                # Adding timestamp ensures that even if we rerun, we don't conflict with internal batch logic
                unique_id = f"{section.law_family}_{section.pdf_filename}_{section.section_number}_{i}_{chunk_idx}"
                ids.append(unique_id)
                documents.append(chunk)
                metadatas.append({
                    "law_family": str(section.law_family),
                    "filename": section.pdf_filename,
                    "section_number": section.section_number,
                    "title": section.title or "",
                    "year": section.year,
                    "is_amendment": section.is_amendment
                })
                chunk_idx += 1
        
        # Batch generate embeddings and add to Chroma
        batch_size = 20
        for i in range(0, len(ids), batch_size):
            logger.info(f"Indexing batch {i // batch_size + 1} of {len(ids) // batch_size + 1}...")
            batch_docs = documents[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            
            # Retry loop for embeddings
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch_docs)
                    self.collection.upsert(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    break # Success!
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 60
                        logger.warning(f"Rate limited on embeddings. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to index batch: {e}")
                        raise e
            
            time.sleep(20) # 20s sleep between successful batches

if __name__ == "__main__":
    vectorizer = LawVectorizer()
