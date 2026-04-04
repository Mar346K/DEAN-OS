import asyncio
import json
import os
import sys
import logging
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import docker

# --- PATH FIX ---
sys.path.append(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.session import get_db
from database.models import TaskTrace
from tasks import execute_assembly_line_task
import valkyrie_crypto
from tools.ast_mapper import ProjectMapper
from agents.librarian import Librarian

logger = logging.getLogger("uvicorn.error")

# --- UTILITY: DATA SANITIZATION ---
def scrub_junk_files(directory: str):
    """Deep searches and destroys .venv, venv, and __pycache__ to protect the Librarian."""
    junk_names = {'.venv', 'venv', '__pycache__', 'node_modules', '.pytest_cache', '.git'}
    print(f"[SYSTEM] 🧹 Initiating Safety Scrub in: {directory}")

    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs:
            if name in junk_names:
                junk_path = os.path.join(root, name)
                try:
                    shutil.rmtree(junk_path)
                    print(f"[CLEANUP] Deleted junk directory: {junk_path}")
                except Exception as e:
                    print(f"[CLEANUP ⚠️] Failed to delete {junk_path}: {e}")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception: # nosec B112
                continue

manager = ConnectionManager()

async def redis_listener():
    try:
        is_local = os.getenv("REDIS_HOST") is None
        redis_host = "127.0.0.1" if is_local else os.getenv("REDIS_HOST")
        redis_port = 6380 if is_local else 6379
        redis_client = aioredis.from_url(f"redis://{redis_host}:{redis_port}/0", decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("ui_broadcasts")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    await manager.broadcast(payload)
                except Exception: pass # nosec B110
            await asyncio.sleep(0.05)
    except asyncio.CancelledError: pass

async def hardware_poller():
    AETHELGARD_URL = f"http://{os.getenv('AETHELGARD_HOST', '127.0.0.1')}:8003/metrics"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(AETHELGARD_URL, timeout=0.5)
                if resp.status_code == 200:
                    await manager.broadcast({"type": "telemetry", "payload": resp.json()})
            except Exception: pass # nosec B110
            await asyncio.sleep(1)

background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller = asyncio.create_task(hardware_poller())
    listener = asyncio.create_task(redis_listener())
    background_tasks.add(poller)
    background_tasks.add(listener)
    yield
    for task in background_tasks: task.cancel()

app = FastAPI(title="DEAN-OS Orchestrator API", lifespan=lifespan)

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)

@app.post("/build")
async def start_build(intent: dict):
    execute_assembly_line_task.delay(intent.get("prompt", ""))
    return {"status": "Assembly Line Queued"}

@app.get("/logs")
async def get_forensic_logs(db: AsyncSession = Depends(get_db)):
    query = select(TaskTrace).order_by(TaskTrace.id.desc()).limit(100)
    result = await db.execute(query)
    traces = result.scalars().all()
    return [{"id": t.id, "run_id": str(t.run_id), "trace_id": t.trace_id, "agent_name": t.agent_name, "action": t.action, "status": t.status, "timestamp": t.timestamp.isoformat(), "logs": t.logs} for t in reversed(traces)]

def _scan_directory(base_path):
    tree = []
    if not os.path.exists(base_path): return tree
    for entry in os.scandir(base_path):
        node = {"name": entry.name, "path": os.path.relpath(entry.path, base_path).replace("\\", "/")}
        if entry.is_dir():
            node["type"] = "folder"
            node["children"] = _scan_directory(entry.path)
        else: node["type"] = "file"
        tree.append(node)
    return sorted(tree, key=lambda x: (x["type"] == "file", x["name"]))

@app.get("/workspace")
async def get_workspace_tree():
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    return _scan_directory(workspace_dir)

@app.post("/workspace/delete")
async def delete_workspace_item(payload: dict):
    target_path = payload.get("path")
    if not target_path or ".." in target_path: return {"status": "error", "message": "Invalid path"}
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    full_path = os.path.abspath(os.path.join(workspace_dir, target_path))
    if not full_path.startswith(workspace_dir): return {"status": "error", "message": "Path traversal blocked"}
    try:
        if os.path.isdir(full_path): shutil.rmtree(full_path)
        elif os.path.isfile(full_path): os.remove(full_path)
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/workspace/prune-venv")
async def prune_workspace_venv():
    workspace_dir = "/app/staging/projects/default/workspace"
    try:
        scrub_junk_files(workspace_dir)
        return {"status": "success", "message": "Workspace curated. Junk removed."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspace/map")
async def trigger_ast_map():
    workspace_dir = "/app/staging/projects/default/workspace"
    mapper = ProjectMapper(workspace_dir)
    graph_data = mapper.generate_ui_graph()
    await manager.broadcast({"type": "ast_map", "payload": graph_data})
    return {"status": "success", "message": "Workspace Bloom triggered"}

@app.post("/ingest")
async def ingest_zip(file: UploadFile = File(...)):
    workspace_dir = "/app/staging/projects/default/workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(workspace_dir, safe_filename)
    with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)

    oubliette_host = os.getenv("OUBLIETTE_HOST", "oubliette")
    secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
    token = valkyrie_crypto.forge_token("intake-forge", "analyzer", secret)

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"http://{oubliette_host}:8002/extract", json={"filename": safe_filename}, headers={"Authorization": f"Bearer {token}"}, timeout=60.0)
        except Exception: return {"status": "error", "message": "Failed to extract in sandbox"}

    if os.path.exists(file_path):
        try: os.remove(file_path)
        except OSError: pass

    # --- [NEW] AUTOMATIC FALLBACK SCRUB ---
    scrub_junk_files(workspace_dir)

    try:
        librarian = Librarian(project_id="default")
        asyncio.create_task(asyncio.to_thread(librarian.process_workspace, workspace_dir))
    except Exception as e: print(f"[INGEST ERROR] Librarian failed to start: {e}")
    return {"status": "success"}

@app.get("/output/tree")
async def get_output_tree():
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    return _scan_directory(workspace_dir)

# --- PHASE 3.5: THE RELEASE VAULT ---

@app.get("/vault/tree")
async def get_vault_tree():
    """Scans the clean room for verified, production-ready code."""
    vault_dir = os.path.abspath("/app/staging/projects/default/release_vault")
    os.makedirs(vault_dir, exist_ok=True)
    return _scan_directory(vault_dir)

@app.post("/vault/read")
async def read_vault_file(payload: dict):
    """Reads a verified file from the Release Vault."""
    target_path = payload.get("path")
    if not target_path or ".." in target_path: return {"status": "error"}

    vault_dir = os.path.abspath("/app/staging/projects/default/release_vault")
    full_path = os.path.abspath(os.path.join(vault_dir, target_path))

    if not full_path.startswith(vault_dir): return {"status": "error"}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return {"status": "success", "content": f.read()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/file/read")
async def read_file(payload: dict):
    target_path = payload.get("path")
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    full_path = os.path.abspath(os.path.join(workspace_dir, target_path))
    if not full_path.startswith(workspace_dir): return {"status": "error"}
    try:
        with open(full_path, "r", encoding="utf-8") as f: return {"status": "success", "content": f.read()}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/file/write")
async def write_file(payload: dict):
    target_path = payload.get("path")
    content = payload.get("content", "")
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    full_path = os.path.abspath(os.path.join(workspace_dir, target_path))
    if not full_path.startswith(workspace_dir): return {"status": "error"}
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f: f.write(content)
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/output/map")
async def trigger_output_map():
    workspace_dir = "/app/staging/projects/default/workspace"
    mapper = ProjectMapper(workspace_dir)
    await manager.broadcast({"type": "ast_map", "payload": mapper.generate_ui_graph()})
    return {"status": "success"}

@app.post("/staging/purge")
async def purge_staging():
    workspace_dir = os.path.abspath("/app/staging/projects/default/workspace")
    try:
        for item in os.listdir(workspace_dir):
            item_path = os.path.join(workspace_dir, item)
            if os.path.isdir(item_path): shutil.rmtree(item_path)
            else: os.remove(item_path)
        await manager.broadcast({"type": "staging_log", "payload": {"type": "system", "text": "--- STAGING WORKSPACE PURGED ---"}})
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/staging/kill")
async def kill_swarm():
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_client = aioredis.from_url(f"redis://{redis_host}:6379/0", decode_responses=True)
        await redis_client.flushdb()
        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-KILL", "agent": "Manager", "action": "💀 BRUTE FORCE KILL: Redis Queues Flushed. Swarm Halted.", "status": "error"}})
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/hitl/resolve")
async def resolve_hitl(payload: dict):
    filename = payload.get("filename", "unknown")
    await manager.broadcast({"type": "staging_log", "payload": {"type": "system", "text": f"--- HITL FIX APPLIED TO {filename}. WAKING SWARM... ---"}})
    return {"status": "success"}

@app.post("/settings/keys")
async def save_api_key(payload: dict):
    provider, api_key = payload.get("provider"), payload.get("api_key")
    if not provider or not api_key: return {"status": "error", "message": "Missing key data"}
    secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
    if valkyrie_crypto.seal_key(provider, api_key, secret):
        logger.info(f"[SECURITY] {provider} API key successfully vaulted.")
        return {"status": "success", "message": f"{provider} key sealed."}
    return {"status": "error", "message": "Vault encryption failed."}

@app.post("/settings/budget")
async def update_budget(payload: dict):
    limit = payload.get("limit", 1.00)
    try:
        with open("/app/infrastructure/budget.yaml", "w", encoding="utf-8") as f:
            f.write(f"# DEAN-OS FinOps Guardrails\ntask_limit_usd: {float(limit):.2f}\n")
        logger.info(f"[FINOPS] Budget limit updated to ${float(limit):.2f}")
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.get("/system/logs/{service}")
async def get_system_logs(service: str):
    try:
        client = docker.from_env()
        logs = client.containers.get(f"deanos_{service}").logs(tail=200, stdout=True, stderr=True).decode('utf-8', errors='ignore')
        return {"status": "success", "logs": logs}
    except Exception as e: return {"status": "error", "logs": f"Failed to retrieve logs for {service}: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # nosec B104
