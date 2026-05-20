import chromadb
from typing import List, Dict
from app.config import settings
from app.agent.core.embeddings import get_resilient_embeddings

class LawRetriever:
    def __init__(self):
        import os
        import shutil
        try:
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self.collection = self.client.get_collection(name="pakistan_family_laws")
        except Exception as e:
            # If the database is corrupted or doesn't exist, try to recreate it
            print(f"Error initializing ChromaDB: {e}. Recreating database directory...")
            try:
                if os.path.exists(settings.CHROMA_PERSIST_DIR):
                    if os.path.isdir(settings.CHROMA_PERSIST_DIR):
                        shutil.rmtree(settings.CHROMA_PERSIST_DIR)
                    else:
                        os.remove(settings.CHROMA_PERSIST_DIR)
                os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
                self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                self.collection = self.client.get_or_create_collection(name="pakistan_family_laws")
            except Exception as re_err:
                print(f"Failed to auto-heal ChromaDB: {re_err}")
                raise re_err
        
        self.embeddings = get_resilient_embeddings()

    def retrieve(self, query: str, families: List[str], k: int = 5) -> List[Dict]:
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search ChromaDB
        # filter by relevant families if provided
        where_filter = None
        if families:
            if len(families) == 1:
                where_filter = {"law_family": families[0]}
            else:
                where_filter = {"law_family": {"$in": families}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        retrieved_docs = []
        for i in range(len(results["ids"][0])):
            retrieved_docs.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i]
            })
            
        return retrieved_docs

if __name__ == "__main__":
    retriever = LawRetriever()
    docs = retriever.retrieve("Second marriage procedure", ["muslim_family_laws"])
    for d in docs:
        print(f"[{d['metadata']['filename']}] {d['content'][:100]}...")
