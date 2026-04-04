from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
import valkyrie_crypto
import os
import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Setup logging for the System Health tab
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mnemosyne")

app = FastAPI(title="Mnemosyne Knowledge Vault")

# [TRUTH_SOURCE]: Use environment variable first, then fallback
INTERNAL_SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

logger.info("Loading Neural Embedding Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# [FIX] Connect to the Qdrant CONTAINER ENGINE instead of a local path
qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
logger.info(f"Connecting to Qdrant Engine at: {qdrant_host}:6333")
client = QdrantClient(host=qdrant_host, port=6333)

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
    logger.info(f"Memory requested: '{query}' | Tenant: {project_id}")

    try:
        if not client.collection_exists(COLLECTION_NAME):
            return {"results": [{"text": "Vault is empty. No collections found."}]}

        # 1. Convert text to vector
        query_vector = model.encode(query).tolist()

        # 2. Construct the Tenant Filter
        target_project = project_id if project_id != "default" else "global_docs"
        tenant_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=target_project)
                )
            ]
        )

        # 3. Standardized Search (Talking to the container engine)
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=tenant_filter,
            limit=5
        )

        # 4. Format results
        formatted_results = []
        for hit in search_result:
            formatted_results.append({
                "score": hit.score,
                "source": hit.payload.get("source", "unknown"),
                "text": hit.payload.get("text", "")
            })

        if not formatted_results:
            return {"results": [{"text": f"No specific context found for '{target_project}'."}]}

        return {"results": formatted_results}

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return {"results": [{"text": f"Error accessing memory: {str(e)}"}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # nosec B104
