import asyncio
import json
import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
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

# --- THE SWARM RUNNER ---
async def execute_assembly_line(prompt: str):
    """This runs in the background and executes the actual AI Swarm."""
    await manager.broadcast({
        "type": "agent_trace",
        "payload": {"trace_id": "SYS-001", "agent": "Manager", "action": f"Initiating Assembly Line for: {prompt}", "status": "running"}
    })

    # 1. The Architect
    await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "ARCH-001", "agent": "Architect", "action": "Designing system blueprints...", "status": "running"}})
    architect = Architect()

    # [FIX]: Offload blocking LLM call to a background thread!
    plan = await asyncio.to_thread(architect.draft_plan, prompt)

    if not plan or 'files' not in plan or len(plan['files']) == 0:
        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-ERR", "agent": "System", "action": "Architect failed to generate blueprint.", "status": "error"}})
        return

    target_file = plan['files'][0]
    filename = target_file['filename']

    await manager.broadcast({
        "type": "ast_map",
        "payload": {
            "nodes": [{"id": filename, "group": "python", "churn_score": 1}],
            "edges": []
        }
    })

    # --- THE SELF-HEALING LOOP ---
    MAX_RETRIES = 3
    attempt = 1
    feedback = None

    while attempt <= MAX_RETRIES:
        action_msg = f"Writing implementation for {filename}..." if attempt == 1 else f"Fixing errors in {filename} (Attempt {attempt})..."
        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"CODE-00{attempt}", "agent": "Coder", "action": action_msg, "status": "running"}})

        coder = MainCoder()
        # [FIX]: Threading
        file_path = await asyncio.to_thread(coder.write_module, plan, target_file, feedback, attempt)

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"TEST-00{attempt}", "agent": "Tester", "action": f"Writing adversarial tests (Attempt {attempt})...", "status": "running"}})
        tester = Tester()
        # [FIX]: Threading
        test_file_path = await asyncio.to_thread(tester.write_tests, filename, feedback, attempt)

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"ANAL-00{attempt}", "agent": "Analyzer", "action": "Evaluating in Oubliette Sandbox...", "status": "running"}})
        analyzer = Analyzer()

        test_filename = os.path.basename(test_file_path) if test_file_path else f"test_{filename}"
        # [FIX]: Threading
        report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

        if report.get("status") == "pass":
            # --- PHASE 22: THE DEPLOYER ---
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "DEP-001", "agent": "Deployer", "action": f"Migrating {filename} to production workspace...", "status": "running"}})
            deployer = Deployer()
            prod_path = await asyncio.to_thread(deployer.deploy_module, filename)

            await manager.broadcast({
                "type": "agent_trace",
                "payload": {"trace_id": "SYS-002", "agent": "Manager", "action": f"Assembly Line Complete. {filename} is live in Production.", "status": "running"}
            })

            # --- PHASE 23: LIVE CARTOGRAPHY ---
            # Update the React UI graph with the newly deployed file
            await manager.broadcast({
                "type": "ast_map",
                "payload": {
                    "nodes": [{"id": filename, "group": "python", "churn_score": 0}], # Fresh code has 0 scar tissue!
                    "edges": []
                }
            })
            break
        else:
            feedback = report.get("logs", "Unknown Execution Error")
            await manager.broadcast({
                "type": "agent_trace",
                "payload": {"trace_id": f"SYS-ERR-{attempt}", "agent": "Manager", "action": f"Sandbox rejected code. Extracting logs for self-healing...", "status": "error"}
            })
            attempt += 1

    # --- HUMAN-IN-THE-LOOP (HITL) ESCALATION ---
    if attempt > MAX_RETRIES:
        await manager.broadcast({
            "type": "agent_trace",
            "payload": {"trace_id": "SYS-003", "agent": "Manager", "action": "MAX RETRIES EXCEEDED. Escalating to Human-in-the-Loop.", "status": "error"}
        })

        await manager.broadcast({
            "type": "hitl_alert",
            "payload": {
                "trace_id": "SYS-001",
                "filename": filename,
                "attempt": MAX_RETRIES,
                "error_traceback": feedback[-500:] if feedback else "Unknown systemic failure.",
                "action_required": "Provide a hint to fix this or press Quarantine."
            }
        })

# --- THE NEURAL OVERRIDE (HITL RECOVERY) ---
async def execute_recovery_line(filename: str, hint: str, error_log: str):
    """A specialized swarm that injects human feedback directly into the Coder."""
    await manager.broadcast({
        "type": "agent_trace",
        "payload": {"trace_id": "SYS-HITL", "agent": "Manager", "action": f"Neural Override Accepted for {filename}. Re-engaging Swarm...", "status": "running"}
    })

    plan = {"project_name": "Recovery_Protocol", "files": [{"filename": filename, "purpose": "Apply human fix", "signatures": []}]}
    target_file = plan["files"][0]
    feedback_payload = f"PREVIOUS ERROR:\n{error_log}\n\nLEAD ENGINEER OVERRIDE (CRITICAL HINT):\n{hint}"

    await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "CODE-REC", "agent": "Coder", "action": "Applying human fix...", "status": "running"}})
    coder = MainCoder()
    # [FIX]: Threading
    file_path = await asyncio.to_thread(coder.write_module, plan, target_file, feedback_payload, 4)

    await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "TEST-REC", "agent": "Tester", "action": "Validating human fix...", "status": "running"}})
    tester = Tester()
    # [FIX]: Threading
    test_file_path = await asyncio.to_thread(tester.write_tests, filename, "Ensure tests accommodate the human's logic changes.", 4)

    await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "ANAL-REC", "agent": "Analyzer", "action": "Evaluating fixed code in Sandbox...", "status": "running"}})
    analyzer = Analyzer()
    test_filename = os.path.basename(test_file_path) if test_file_path else f"test_{filename}"
    # [FIX]: Threading
    report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

    if report.get("status") == "pass":
            # --- PHASE 22: THE DEPLOYER ---
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "DEP-001", "agent": "Deployer", "action": f"Migrating {filename} to production workspace...", "status": "running"}})
            deployer = Deployer()
            prod_path = await asyncio.to_thread(deployer.deploy_module, filename)

            await manager.broadcast({
                "type": "agent_trace",
                "payload": {"trace_id": "SYS-002", "agent": "Manager", "action": f"Assembly Line Complete. {filename} is live in Production.", "status": "running"}
            })

            # --- PHASE 23: LIVE CARTOGRAPHY ---
            # Update the React UI graph with the newly deployed file
            await manager.broadcast({
                "type": "ast_map",
                "payload": {
                    "nodes": [{"id": filename, "group": "python", "churn_score": 0}], # Fresh code has 0 scar tissue!
                    "edges": []
                }
            })
    else:
        await manager.broadcast({
            "type": "hitl_alert",
            "payload": {
                "trace_id": "SYS-HITL-FAIL",
                "filename": filename,
                "attempt": "RECOVERY",
                "error_traceback": report.get("logs", "")[-500:],
                "action_required": "Recovery failed. Provide another hint."
            }
        })

# --- THE TRIGGER ---
@app.post("/build")
async def start_build(intent: dict, background_tasks: BackgroundTasks):
    prompt = intent.get("prompt", "No prompt provided.")
    # Hand the heavy lifting off to a background thread so the API stays responsive
    background_tasks.add_task(execute_assembly_line, prompt)
    return {"status": "Assembly Line Queued"}

# --- THE HITL TRIGGER ---
@app.post("/hitl/resolve")
async def resolve_hitl(intent: dict, background_tasks: BackgroundTasks):
    filename = intent.get("filename")
    hint = intent.get("hint")
    error_log = intent.get("error_traceback")

    # Hand the recovery line off to the background thread
    background_tasks.add_task(execute_recovery_line, filename, hint, error_log)
    return {"status": "Recovery Swarm Deployed"}

if __name__ == "__main__":
    import uvicorn
    # Start the server on 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
