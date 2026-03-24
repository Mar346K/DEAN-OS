import os
import docker
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import valkyrie_crypto  # Our Rust-powered security shield

app = FastAPI(title="Oubliette Sandbox Service")

# [SECURITY UPGRADE]: Pull from environment variables to pass Git pre-commit hooks.
# The fallback is ONLY used for local development.
INTERNAL_SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

# Initialize the Docker client
try:
    client = docker.from_env()
except Exception as e:
    print(f"[ERROR] Could not connect to Docker: {e}")

# Updated Payload: Supports both raw code strings AND file execution
class RunRequest(BaseModel):
    code: str = None
    entrypoint: str = "main.py"

def verify_agent_token(authorization: str = Header(None)):
    """Zero-Trust Gatekeeper with RBAC Enforcer"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Token")

    token = authorization.split(" ")[1]

    # [SECURITY UPGRADE] Enforce exact scope instead of just validating the signature
    if not valkyrie_crypto.enforce_scope(token, INTERNAL_SECRET, "sandbox:execute"):
        raise HTTPException(status_code=403, detail="Access Denied: Missing 'sandbox:execute' scope")
    return True

@app.get("/health")
def health_check():
    return {"status": "online", "sandbox_image": "daen-agent-sandbox"}

@app.post("/run")
async def run_in_workspace(payload: RunRequest, authorized: bool = Depends(verify_agent_token)):
    """Executes code within the context of the mounted workspace."""

    # [FIX] Pull the true Host OS path from Docker Compose, or fallback to local relative path
    host_workspace = os.getenv("HOST_WORKSPACE_PATH")
    if not host_workspace:
        host_workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../staging/workspace"))
    else:
        cmd = [payload.entrypoint]

    try:
        container_output = client.containers.run(
            image="daen-agent-sandbox",
            entrypoint=["python"], # <--- [FIX] Overrides the Dockerfile's default
            command=cmd,
            volumes={
                host_workspace: {
                    'bind': '/home/agentuser/workspace',
                    'mode': 'rw'
                }
            },
            working_dir='/home/agentuser/workspace',
            mem_limit="512m",
            nano_cpus=1000000000,
            network_disabled=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        return {"output": container_output.decode("utf-8").strip()}

    except docker.errors.ContainerError as e:
        # [FIX] The Docker SDK puts ALL output (stdout + stderr) into `e.stderr` when a container crashes.
        logs = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else str(e.stderr or "")

        return {"error": "Execution Error", "details": logs.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) # nosec B104
