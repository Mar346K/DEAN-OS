import asyncio
import json
import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Ensure we can import our agents
sys.path.append(os.path.dirname(__file__))

from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer
from telemetry.tracer import TelemetryEngine
from telemetry.watchdog import SystemWatchdog

app = FastAPI(title="DEAN-OS Orchestrator")

# Enable CORS so the React dev server can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] UI Client Connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception: # nosec B112
                continue

manager = ConnectionManager()

# --- THE TELEMETRY BRIDGE ---
async def hardware_poller():
    """Polls Aethelgard (Rust) and broadcasts to UI via WebSockets."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Hit the Rust Governor
                resp = await client.get("http://127.0.0.1:8003/metrics", timeout=0.5)
                if resp.status_code == 200:
                    metrics = resp.json()
                    await manager.broadcast({
                        "type": "telemetry",
                        "payload": metrics
                    })
            except Exception as e: # nosec B110
                pass # Aethelgard might be offline
            await asyncio.sleep(1) # 1Hz refresh rate

@app.on_event("startup")
async def startup_event():
    # Start the hardware background poller
    asyncio.create_task(hardware_poller())
    print("[MANAGER] WebSocket bridge initialized.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from the UI (like HITL fixes)
            data = await websocket.receive_text()
            print(f"[WS] Received from UI: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[WS] UI Client Disconnected.")

# --- THE TRIGGER ---
@app.post("/build")
async def start_build(intent: dict):
    # This is where we will trigger the AssemblyLine in Phase 20!
    # For now, just a heartbeat for the UI
    await manager.broadcast({
        "type": "agent_trace",
        "payload": {
            "trace_id": "INIT",
            "agent": "System",
            "action": f"Received intent: {intent.get('prompt')}",
            "status": "running"
        }
    })
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    # Start the server on 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
