import os
import docker
import zipfile
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import valkyrie_crypto

# Setup detailed logging for the Health Tab
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oubliette")

app = FastAPI(title="Oubliette Sandbox Service")
INTERNAL_SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

try:
    client = docker.from_env()
    logger.info("[SYSTEM] Connected to Docker Daemon.")
except Exception as e:
    logger.error(f"[ERROR] Could not connect to Docker: {e}")

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

@app.get("/health")
async def health_check():
    return {"status": "online", "modules": ["run", "extract"]}

@app.post("/run")
async def run_in_workspace(payload: RunRequest, authorized: bool = Depends(verify_agent_token)):
    logger.info(f"Received execution request for project: {payload.project_id}")

    # [CRITICAL FIX] Docker-in-Docker requires the absolute HOST machine path to mount volumes!
    host_base = os.getenv("HOST_STAGING_PATH")
    if not host_base:
        raise HTTPException(status_code=500, detail="HOST_STAGING_PATH environment variable missing.")

    host_workspace = os.path.join(host_base, payload.project_id, "workspace")

    # --- ADD THESE THREE LINES ---
    logger.info(f"[DIAGNOSTIC] HOST_STAGING_PATH is: {host_base}")
    logger.info(f"[DIAGNOSTIC] Attempting to mount: {host_workspace}")
    logger.info(f"[DIAGNOSTIC] Target project: {payload.project_id}")
    # -----------------------------

    cmd = ["-c", payload.code] if payload.code else [payload.entrypoint]

    try:
        # Micro-Ephemeral Execution: spins up, runs, and is instantly destroyed
        container_output = client.containers.run(
            image="daen-agent-sandbox",
            entrypoint=["python"],
            command=cmd,
            volumes={ host_workspace: {'bind': '/home/agentuser/workspace', 'mode': 'rw'} },
            working_dir='/home/agentuser/workspace',
            mem_limit="512m",
            network_disabled=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        return {"output": container_output.decode("utf-8").strip()}

    except docker.errors.ContainerError as e:
        # We MUST catch ContainerError to return the Pytest failure text to the Analyzer!
        logs = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else str(e.stderr or "")
        return {"error": "Execution Error", "details": logs.strip()}
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract")
async def extract_archive(payload: dict, authorized: bool = Depends(verify_agent_token)):
    """Safely extracts a ZIP file inside the isolated staging directory."""
    filename = payload.get("filename")
    project_id = payload.get("project_id", "default")

    logger.info(f"📦 Extraction requested: {filename} for project {project_id}")

    if not filename or ".." in filename or not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # [FIX] Use the internal mount path defined in docker-compose
    workspace_dir = f"/app/staging/projects/{project_id}/workspace"
    file_path = os.path.join(workspace_dir, filename)

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Archive not found at {file_path}")

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.startswith("/") or ".." in member:
                    raise Exception("Zip Slip Vulnerability Detected.")
            zip_ref.extractall(workspace_dir)

        logger.info(f"✅ Successfully extracted {filename}")
        return {"status": "success", "message": f"Extracted {filename}"}
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
