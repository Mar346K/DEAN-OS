import os
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import valkyrie_crypto  # Our Rust-powered security layer

# --- 1. CORE INITIALIZATION ---
app = FastAPI(title="Mnemosyne Memory Vault")

# [TRUTH_SOURCE]: Shared internal secret. Match this in your tests!
INTERNAL_SECRET = "daen-internal-dev-secret-2026"  # nosec B105

# Load the neural model and connect to the local Qdrant database
print("[SYSTEM] Loading neural embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(path="./storage/qdrant_db")

# --- 2. DATA MODELS ---
class IngestRequest(BaseModel):
    file_name: str
    content: str

# --- 3. SECURITY DEPENDENCY ---
def verify_agent_token(authorization: str = Header(None)):
    """Zero-Trust Gatekeeper"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Token")

    token = authorization.split(" ")[1]
    # Call our Rust function for memory-safe, high-speed validation
    if not valkyrie_crypto.validate_token(token, INTERNAL_SECRET):
        raise HTTPException(status_code=403, detail="Invalid or Expired Token")
    return True

# --- 4. ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "online", "vault": "active"}

@app.post("/ingest")
async def ingest_document(data: IngestRequest, _=Depends(verify_agent_token)):
    """API-based ingestion to avoid file-lock collisions with the local DB."""
    if not client.collection_exists("daen_docs"):
        client.create_collection(
            collection_name="daen_docs",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    # Chunk text by double newline (paragraphs)
    chunks = [c.strip() for c in data.content.split("\n\n") if len(c.strip()) > 20]
    points = []

    # Simple ID counter based on existing points
    collection_info = client.get_collection("daen_docs")
    start_id = collection_info.points_count + 1

    for i, chunk in enumerate(chunks):
        vector = model.encode(chunk).tolist()
        points.append(PointStruct(
            id=start_id + i,
            vector=vector,
            payload={"source": data.file_name, "text": chunk}
        ))

    client.upsert(collection_name="daen_docs", points=points)
    return {"status": "success", "inserted_chunks": len(points)}

@app.post("/search")
async def search_vault(query: str, authorized: bool = Depends(verify_agent_token)):
    """Authorized RAG search against the project documentation."""
    try:
        if not client.collection_exists("daen_docs"):
            return {"query": query, "results": [], "note": "Collection 'daen_docs' does not exist."}

        # 1. Vectorize query
        query_vector = model.encode(query).tolist()

        # 2. Query Qdrant using the modern 'query_points' method
        search_result = client.query_points(
            collection_name="daen_docs",
            query=query_vector,
            limit=3
        ).points

        # 3. Format results
        results = [
            {"text": res.payload["text"], "source": res.payload["source"], "score": res.score}
            for res in search_result
        ]

        return {"query": query, "results": results}
    except Exception as e:
        print(f"[CRITICAL ERROR] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Start the Librarian on her dedicated port
    uvicorn.run(app, host="127.0.0.1", port=8001)
