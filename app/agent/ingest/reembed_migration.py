import os
import chromadb
from app.config import settings
from app.agent.core.embeddings import get_resilient_embeddings

def migrate_database():
    print(f"Loading database from: {settings.CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    
    try:
        col = client.get_collection("pakistan_family_laws")
        count = col.count()
        print(f"Found existing collection with {count} documents.")
        
        if count == 0:
            print("Collection is empty. Nothing to migrate.")
            return
            
        # Get all documents with their metadatas
        all_data = col.get(include=["documents", "metadatas"])
        ids = all_data["ids"]
        documents = all_data["documents"]
        metadatas = all_data["metadatas"]
        print(f"Successfully extracted {len(ids)} documents from old database.")
        
        # Now delete the collection
        client.delete_collection("pakistan_family_laws")
        print("Deleted old collection.")
        
    except Exception as e:
        print(f"No existing collection found or error reading: {e}")
        return

    # Recreate the collection
    col = client.get_or_create_collection("pakistan_family_laws")
    print("Recreated collection 'pakistan_family_laws'.")
    
    # Get embeddings
    embedder = get_resilient_embeddings()
    
    # Generate new embeddings and insert in batches
    batch_size = 20
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        
        print(f"Indexing batch {i // batch_size + 1} of {len(ids) // batch_size + 1}...")
        batch_embeddings = embedder.embed_documents(batch_docs)
        
        col.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_docs,
            metadatas=batch_metas
        )
        
    print("Migration completed successfully! All documents re-embedded with 384 dimensions.")

if __name__ == "__main__":
    migrate_database()
