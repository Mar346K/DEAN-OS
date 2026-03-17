import os
import docker
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import valkyrie_crypto  # Our Rust-powered security shield

app = FastAPI(title="Oubliette Sandbox Service")

# [TRUTH_SOURCE]: Must match the secret in Mnemosyne and Valkyrie
INTERNAL_SECRET = "daen-internal-dev-secret-2026"  # nosec B105

# Initialize the Docker client
try:
    client = docker.from_env()
except Exception as e:
    print(f"[ERROR] Could not connect to Docker: {e}")

# Tell FastAPI to expect a JSON object with a "code" string
class CodePayload(BaseModel):
    code: str

def verify_agent_token(authorization: str = Header(None)):
    """Zero-Trust Gatekeeper"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Token")

    token = authorization.split(" ")[1]
    if not valkyrie_crypto.validate_token(token, INTERNAL_SECRET):
        raise HTTPException(status_code=403, detail="Invalid Token")
    return True

@app.get("/health")
def health_check():
    return {"status": "online", "sandbox_image": "daen-agent-sandbox"}

@app.post("/run")
async def run_code(payload: CodePayload, authorized: bool = Depends(verify_agent_token)):
    """Execute Python code inside the isolated Oubliette cell."""
    try:
        container_output = client.containers.run(
            image="daen-agent-sandbox",
            command=[payload.code], # The safe array format using Pydantic
            mem_limit="512m",
            nano_cpus=1000000000,
            network_disabled=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        return {"output": container_output.decode("utf-8").strip()}

    except docker.errors.ContainerError as e:
        # This captures the traceback from INSIDE the box
        return {"error": "Execution Error", "details": e.stderr.decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
