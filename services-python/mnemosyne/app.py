from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
import valkyrie_crypto
import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
# [NEW] Import the Qdrant filtering models
from qdrant_client.models import Filter, FieldCondition, MatchValue

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
async def search_memory(query: str, project_id: str = "default", authorized: bool = Depends(verify_agent_token)):
    """Retrieve context for the Sycophant Brain using Vector Similarity."""
    print(f"[MNEMOSYNE] Memory requested for query: '{query}' | Tenant: {project_id}")

    try:
        if not client.collection_exists(COLLECTION_NAME):
            return {"results": [{"text": "Vault is empty. No collections found."}]}

        # 1. Convert the AI's text query into a mathematical vector
        query_vector = model.encode(query).tolist()

        # [NEW] Construct the Tenant Filter
        # If no specific project is requested, we default to the global documentation
        target_project = project_id if project_id != "default" else "global_docs"

        tenant_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=target_project)
                )
            ]
        )

        # 2. Search Qdrant for the closest conceptual matches (Modern API)
        try:
            response = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=tenant_filter,
                limit=3
            )
            search_result = response.points
        except AttributeError:
            # Fallback for older Qdrant versions
            search_result = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=tenant_filter,
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
            return {"results": [{"text": f"No specific context found in Vault for tenant '{target_project}'."}]}

        return {"results": formatted_results}

    except Exception as e:
        print(f"[MNEMOSYNE] Search Error: {e}")
        return {"results": [{"text": f"Error accessing memory: {e}"}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # nosec B104
