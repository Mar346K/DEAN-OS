import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Initialize Hardware & Vault
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(path="./storage/qdrant_db")
COLLECTION_NAME = "daen_docs"

def initialize_vault():
    """Create the collection if it doesn't exist."""
    if not client.collection_exists(COLLECTION_NAME):
        print(f"[VAULT] Initializing new collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def ingest_docs():
    """Crawl the root directory for technical documentation."""
    docs_to_read = ["README.md", "ARCHITECTURE.md", "SECURITY.md"]
    points = []
    idx = 1

    for file_path in docs_to_read:
        if os.path.exists(file_path):
            print(f"[INGEST] Processing {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Simple Chunking: Split by double newline to keep paragraphs together
                chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 20]

                for chunk in chunks:
                    # [TRUTH_SOURCE]: Convert text to 384-dimensional vector
                    vector = model.encode(chunk).tolist()
                    points.append(PointStruct(
                        id=idx,
                        vector=vector,
                        payload={"source": file_path, "text": chunk}
                    ))
                    idx += 1

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[SUCCESS] Ingested {len(points)} knowledge points into the vault.")

if __name__ == "__main__":
    initialize_vault()
    ingest_docs()
