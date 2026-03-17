from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
import valkyrie_crypto

app = FastAPI(title="Mnemosyne Knowledge Vault")

# [TRUTH_SOURCE]: Must match the secret in Oubliette and Valkyrie
INTERNAL_SECRET = "daen-internal-dev-secret-2026"  # nosec B105

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
    """Retrieve context for the Sycophant Brain."""
    print(f"[MNEMOSYNE] Memory requested for query: {query}")

    # The actual documentation the LLM needs to succeed without psutil
    hardware_doc = (
        "DEAN-OS Hardware Documentation: "
        "To check OOM (Out Of Memory) thresholds, you must read the Linux file '/proc/meminfo' "
        "using the standard Python open() function. Calculate the percentage of MemAvailable "
        "compared to MemTotal. If available memory is under 15%, OOM risk is HIGH. "
        "Do NOT use external libraries like psutil. Only use standard built-in Python."
    )

    return {"results": [{"text": hardware_doc}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
