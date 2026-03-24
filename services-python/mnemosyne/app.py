from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
import valkyrie_crypto
import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Mnemosyne Knowledge Vault")

# [TRUTH_SOURCE]: Must match the secret in Oubliette and Valkyrie
INTERNAL_SECRET = "daen-internal-dev-secret-2026"  # nosec B105

print("[MNEMOSYNE] Loading Neural Embedding Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Calculate absolute path to the vector DB
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/qdrant_db"))
print(f"[MNEMOSYNE] Connecting to Qdrant Vault at: {db_path}")
client = QdrantClient(path=db_path)
COLLECTION_NAME = "daen_docs"

def verify_agent_token(authorization: str = Header(None)):
    """Zero-Trust Gatekeeper"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Token")
    token = authorization.split(" ")[1]
    if not valkyrie_crypto.validate_token(token, INTERNAL_SECRET):
        raise HTTPException(status_code=403, detail="Invalid Token")
    return True

@app.post("/search")
async def search_memory(query: str, authorized: bool = Depends(verify_agent_token)):
    """Retrieve context for the Sycophant Brain using Vector Similarity."""
    print(f"[MNEMOSYNE] Memory requested for query: '{query}'")

    try:
        if not client.collection_exists(COLLECTION_NAME):
            return {"results": [{"text": "Vault is empty. No collections found."}]}

        # 1. Convert the AI's text query into a mathematical vector
        query_vector = model.encode(query).tolist()

        # 2. Search Qdrant for the closest conceptual matches (Modern API)
        try:
            response = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=3
            )
            search_result = response.points
        except AttributeError:
            # Fallback just in case
            search_result = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=3
            )

        # 3. Format results for the Brain
        formatted_results = []
        for hit in search_result:
            formatted_results.append({
                "score": hit.score,
                "source": hit.payload.get("source", "unknown"),
                "text": hit.payload.get("text", "")
            })

        if not formatted_results:
            return {"results": [{"text": "No specific context found in Vault."}]}

        return {"results": formatted_results}

    except Exception as e:
        print(f"[MNEMOSYNE] Search Error: {e}")
        return {"results": [{"text": f"Error accessing memory: {e}"}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # nosec B104
