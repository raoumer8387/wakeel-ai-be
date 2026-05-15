import chromadb
from typing import List, Dict
from app.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class LawRetriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_collection(name="pakistan_family_laws")
        
        # Use the same embeddings as ingestion
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )

    def retrieve(self, query: str, families: List[str], k: int = 5) -> List[Dict]:
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search ChromaDB
        # filter by relevant families if provided
        where_filter = {}
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
