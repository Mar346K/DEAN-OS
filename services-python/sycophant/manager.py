import asyncio
import json
import os
import sys
import logging
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import httpx
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(__file__))
from database.session import get_db
from database.models import TaskTrace
from tasks import execute_assembly_line_task
import valkyrie_crypto
from tools.ast_mapper import ProjectMapper

logger = logging.getLogger("uvicorn.error")

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
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_client = aioredis.from_url(f"redis://{redis_host}:6379/0", decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("ui_broadcasts")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    await manager.broadcast(payload)
                except Exception: # nosec B110
                    pass
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        pass

async def hardware_poller():
    AETHELGARD_URL = f"http://{os.getenv('AETHELGARD_HOST', '127.0.0.1')}:8003/metrics"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(AETHELGARD_URL, timeout=0.5)
                if resp.status_code == 200:
                    await manager.broadcast({"type": "telemetry", "payload": resp.json()})
            except Exception: # nosec B110
                pass
            await asyncio.sleep(1)

background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller = asyncio.create_task(hardware_poller())
    listener = asyncio.create_task(redis_listener())
    background_tasks.add(poller)
    background_tasks.add(listener)
    yield
    for task in background_tasks:
        task.cancel()

app = FastAPI(title="DEAN-OS Orchestrator API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/build")
async def start_build(intent: dict):
    execute_assembly_line_task.delay(intent.get("prompt", ""))
    return {"status": "Assembly Line Queued"}

@app.get("/logs")
async def get_forensic_logs(db: AsyncSession = Depends(get_db)):
    query = select(TaskTrace).order_by(TaskTrace.id.desc()).limit(100)
    result = await db.execute(query)
    traces = result.scalars().all()
    return [
        {"id": t.id, "run_id": str(t.run_id), "trace_id": t.trace_id, "agent_name": t.agent_name,
         "action": t.action, "status": t.status, "timestamp": t.timestamp.isoformat(), "logs": t.logs}
        for t in reversed(traces)
    ]

# --- PHASE 2.5: INTERACTIVE INTAKE ENDPOINTS ---
def _scan_directory(base_path):
    tree = []
    if not os.path.exists(base_path): return tree
    for entry in os.scandir(base_path):
        node = {"name": entry.name, "path": os.path.relpath(entry.path, base_path).replace("\\", "/")}
        if entry.is_dir():
            node["type"] = "folder"
            node["children"] = _scan_directory(entry.path)
        else:
            node["type"] = "file"
        tree.append(node)
    return sorted(tree, key=lambda x: (x["type"] == "file", x["name"]))

@app.get("/workspace")
async def get_workspace_tree():
    workspace_dir = os.path.abspath("/app/staging/workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    return _scan_directory(workspace_dir)

@app.post("/workspace/delete")
async def delete_workspace_item(payload: dict):
    target_path = payload.get("path")
    if not target_path or ".." in target_path: return {"status": "error", "message": "Invalid path"}
    workspace_dir = os.path.abspath("/app/staging/workspace")
    full_path = os.path.abspath(os.path.join(workspace_dir, target_path))
    if not full_path.startswith(workspace_dir): return {"status": "error", "message": "Path traversal blocked"}
    try:
        if os.path.isdir(full_path): shutil.rmtree(full_path)
        elif os.path.isfile(full_path): os.remove(full_path)
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/workspace/map")
async def trigger_ast_map():
    workspace_dir = "/app/staging/workspace"
    mapper = ProjectMapper(workspace_dir)
    graph_data = mapper.generate_ui_graph()
    await manager.broadcast({"type": "ast_map", "payload": graph_data})
    return {"status": "success", "message": "Workspace Bloom triggered"}

@app.post("/ingest")
async def ingest_zip(file: UploadFile = File(...)):
    workspace_dir = "/app/staging/workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(workspace_dir, safe_filename)
    with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    
    oubliette_host = os.getenv("OUBLIETTE_HOST", "127.0.0.1")
    secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
    token = valkyrie_crypto.forge_token("intake-forge", "analyzer", secret)
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"http://{oubliette_host}:8002/extract", json={"filename": safe_filename}, headers={"Authorization": f"Bearer {token}"}, timeout=30.0)
        except Exception: return {"status": "error", "message": "Failed to extract in sandbox"}
    if os.path.exists(file_path):
        try: os.remove(file_path)
        except OSError: pass
    return {"status": "success"}

# --- PHASE 3: ASSEMBLY LINE & OUTPUT ENDPOINTS ---
@app.get("/output/tree")
async def get_output_tree():
    output_dir = os.path.abspath("/app/staging/output")
    os.makedirs(output_dir, exist_ok=True)
    return _scan_directory(output_dir)

@app.post("/file/read")
async def read_file(payload: dict):
    target_path = payload.get("path")
    if not target_path or ".." in target_path: return {"status": "error"}
    output_dir = os.path.abspath("/app/staging/output")
    full_path = os.path.abspath(os.path.join(output_dir, target_path))
    if not full_path.startswith(output_dir): return {"status": "error"}
    try:
        with open(full_path, "r", encoding="utf-8") as f: return {"status": "success", "content": f.read()}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/file/write")
async def write_file(payload: dict):
    target_path = payload.get("path")
    content = payload.get("content", "")
    if not target_path or ".." in target_path: return {"status": "error"}
    
    output_dir = os.path.abspath("/app/staging/output")
    full_path = os.path.abspath(os.path.join(output_dir, target_path))
    if not full_path.startswith(output_dir): return {"status": "error"}
    
    try:
        # [NEW] Create directories if the Swarm forgot to make them
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f: 
            f.write(content)
        return {"status": "success"}
    except Exception as e: 
        return {"status": "error", "message": str(e)}

@app.post("/output/map")
async def trigger_output_map():
    output_dir = "/app/staging/output"
    os.makedirs(output_dir, exist_ok=True)
    mapper = ProjectMapper(output_dir)
    await manager.broadcast({"type": "ast_map", "payload": mapper.generate_ui_graph()})
    return {"status": "success"}

# --- HITL RESOLUTION ENDPOINT ---
@app.post("/hitl/resolve")
async def resolve_hitl(payload: dict):
    """Called when the user saves a fix for a quarantined file."""
    filename = payload.get("filename", "unknown")
    logger.info(f"HITL override submitted for {filename}")
    
    # Broadcast to the Swarm Monologue that the human has intervened
    await manager.broadcast({
        "type": "staging_log",
        "payload": {
            "type": "system",
            "text": f"--- HITL FIX APPLIED TO {filename}. WAKING SWARM... ---"
        }
    })
    
    # In the future, this is where we will publish back to Redis to unblock the halted agent workflow!
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104