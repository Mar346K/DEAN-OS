import asyncio
import json
import os
import sys
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(__file__))
from tasks import execute_assembly_line_task

# Hijack Uvicorn's native logger so our messages NEVER get buffered or hidden
logger = logging.getLogger("uvicorn.error")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WS] UI Client Connected. Total: {len(self.active_connections)}")

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

# --- BACKGROUND WORKERS ---
async def redis_listener():
    logger.info("[REDIS] Starting listener thread...")
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_url = f"redis://{redis_host}:6379/0"

        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("ui_broadcasts")
        logger.info("[REDIS] Successfully subscribed to 'ui_broadcasts'.")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    trace_id = payload.get("payload", {}).get("trace_id", "SYS")
                    logger.info(f"[REDIS] Broadcasting to UI: {trace_id}")
                    await manager.broadcast(payload)
                except Exception as e:
                    logger.error(f"[REDIS ERROR] Broadcast failed: {e}")
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        logger.info("[REDIS] Thread stopped cleanly.")
    except Exception as e:
        logger.error(f"[REDIS CRITICAL ERROR] Thread died: {e}")

async def hardware_poller():
    logger.info("[HARDWARE] Starting poller thread...")
    AETHELGARD_HOST = os.getenv("AETHELGARD_HOST", "127.0.0.1")
    AETHELGARD_URL = f"http://{AETHELGARD_HOST}:8003/metrics"

    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(AETHELGARD_URL, timeout=0.5)
                if resp.status_code == 200:
                    metrics = resp.json()
                    await manager.broadcast({"type": "telemetry", "payload": metrics})
            except asyncio.CancelledError:
                logger.info("[HARDWARE] Poller stopped cleanly.")
                break
            except Exception: # nosec B110
                pass
            await asyncio.sleep(1)

# --- MODERN LIFESPAN ---
background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[MANAGER] Booting system and background tasks...")

    # Create tasks and keep strong references
    poller = asyncio.create_task(hardware_poller())
    listener = asyncio.create_task(redis_listener())

    background_tasks.add(poller)
    background_tasks.add(listener)

    logger.info("[MANAGER] All background workers initialized.")

    yield # Hand control to FastAPI

    logger.info("[MANAGER] Shutting down workers...")
    for task in background_tasks:
        task.cancel()

app = FastAPI(title="DEAN-OS Orchestrator API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("[WS] UI Client Disconnected.")

@app.post("/build")
async def start_build(intent: dict):
    prompt = intent.get("prompt", "No prompt provided.")
    logger.info(f"[API] Received build request. Dispatching to Celery: {prompt[:30]}...")
    execute_assembly_line_task.delay(prompt)
    return {"status": "Assembly Line Queued via Celery"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
