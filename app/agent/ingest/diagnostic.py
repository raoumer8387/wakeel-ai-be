import chromadb
from app.config import settings

def run_diagnostic():
    print(f"Checking Database at: {settings.CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    
    try:
        col = client.get_collection("pakistan_family_laws")
        count = col.count()
        print(f"✅ SUCCESS: Found collection 'pakistan_family_laws'")
        print(f"📊 DOCUMENT COUNT: {count}")
        
        if count > 0:
            print("\n--- SAMPLE DATA ---")
            results = col.peek(limit=1)
            print(f"Sample ID: {results['ids'][0]}")
            print(f"Sample Metadata: {results['metadatas'][0]}")
        else:
            print("\n❌ WARNING: The collection exists but it is EMPTY.")
            
    except Exception as e:
        print(f"❌ ERROR: Could not find collection. {e}")
        print("Available collections:")
        for c in client.list_collections():
            print(f"- {c.name}")

if __name__ == "__main__":
    run_diagnostic()
