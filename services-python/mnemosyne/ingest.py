import os
import re
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

print("[MNEMOSYNE] Loading Neural Embedding Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(BASE_DIR, "storage", "qdrant_db")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

client = QdrantClient(path=DB_PATH)
COLLECTION_NAME = "daen_docs"

def initialize_vault():
    """Create the collection (and wipe the old one if it exists)."""
    if client.collection_exists(COLLECTION_NAME):
        print(f"[VAULT] Wiping old corrupted memories...")
        client.delete_collection(collection_name=COLLECTION_NAME)

    print(f"[VAULT] Initializing fresh collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

def ingest_docs():
    """Crawl the docs directory for technical documentation."""
    if not os.path.exists(DOCS_DIR):
        print(f"[ERROR] Docs directory not found at {DOCS_DIR}")
        return

    points = []
    idx = 1

    print(f"[INGEST] Scanning {DOCS_DIR} for knowledge...")

    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(DOCS_DIR, filename)

            if os.path.getsize(file_path) == 0:
                continue

            print(f"[INGEST] Absorbing {filename} into memory...")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # SMART CHUNKING: Split when it sees a number "1. " or letter "A. "
                # at the start of a newline to keep entire sections together!
                chunks = [c.strip() for c in re.split(r'\n(?=\d\. |[A-Z]\. )', content) if len(c.strip()) > 20]

                for chunk in chunks:
                    vector = model.encode(chunk).tolist()
                    points.append(PointStruct(
                        id=idx,
                        vector=vector,
                        payload={"source": filename, "text": chunk}
                    ))
                    idx += 1

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[SUCCESS] Ingested {len(points)} knowledge chunks into the Mnemosyne Vault.")

if __name__ == "__main__":
    initialize_vault()
    ingest_docs()
