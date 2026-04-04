import os
import docker
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import valkyrie_crypto

app = FastAPI(title="Oubliette Sandbox Service")
INTERNAL_SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

try:
    client = docker.from_env()
except Exception as e:
    print(f"[ERROR] Could not connect to Docker: {e}")

class RunRequest(BaseModel):
    code: str = None
    entrypoint: str = "main.py"
    project_id: str = "default"

def verify_agent_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Token")
    token = authorization.split(" ")[1]
    if not valkyrie_crypto.enforce_scope(token, INTERNAL_SECRET, "sandbox:execute"):
        raise HTTPException(status_code=403, detail="Access Denied")
    return True

@app.post("/run")
async def run_in_workspace(payload: RunRequest, authorized: bool = Depends(verify_agent_token)):
    # V5.0 SECURE MOUNT PATH
    host_base = os.getenv("HOST_STAGING_PATH")
    if not host_base:
        raise HTTPException(status_code=500, detail="HOST_STAGING_PATH environment variable missing.")

    host_workspace = os.path.join(host_base, payload.project_id, "workspace")

    # Anti-Directory Traversal Check
    if not os.path.abspath(host_workspace).startswith(os.path.abspath(host_base)):
        raise HTTPException(status_code=403, detail="Directory Traversal Blocked")

    os.makedirs(host_workspace, exist_ok=True)
    cmd = ["-c", payload.code] if payload.code else [payload.entrypoint]

    try:
        # Micro-Ephemeral Execution: spins up, runs, and is instantly destroyed
        container_output = client.containers.run(
            image="daen-agent-sandbox",
            entrypoint=["python"],
            command=cmd,
            volumes={
                host_workspace: {'bind': '/home/agentuser/workspace', 'mode': 'rw'}
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
        logs = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else str(e.stderr or "")
        return {"error": "Execution Error", "details": logs.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
