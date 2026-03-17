import docker
from fastapi import FastAPI, HTTPException, Depends, Header
import valkyrie_crypto  # Our Rust security shield
import os

app = FastAPI(title="Oubliette Sandbox Service")

# [TRUTH_SOURCE]: Must match the secret in Mnemosyne and Valkyrie
INTERNAL_SECRET = "daen-internal-dev-secret-2026"  # nosec B105

# Initialize the Docker client
client = docker.from_env()

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
async def run_code(code: str, authorized: bool = Depends(verify_agent_token)):
    """Execute Python code inside the isolated Oubliette cell."""
    try:
        # Run the container with strict resource limits
        container_output = client.containers.run(
            image="daen-agent-sandbox",
            command=code,
            mem_limit="512m",       # Maximum 512MB RAM
            nano_cpus=1000000000,   # Maximum 1 CPU Core
            network_disabled=True,  # No internet access (Zero-Exfiltration)
            remove=True,            # Delete container immediately after finish
            stdout=True,
            stderr=True
        )
        return {"output": container_output.decode("utf-8").strip()}

    except docker.errors.ContainerError as e:
        return {"error": "Execution Error", "details": e.stderr.decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
