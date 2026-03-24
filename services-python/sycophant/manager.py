import asyncio
import json
import os
import sys
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Ensure we can import our agents and database
sys.path.append(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer

# --- NEW: Database Imports ---
from database.session import AsyncSessionLocal
from database.models import SwarmRun, TaskTrace

app = FastAPI(title="DEAN-OS Orchestrator")

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

# --- DATABASE HELPER ---
async def log_trace(db, run_id: uuid.UUID, trace_id: str, agent_name: str, action: str, status: str, logs: str = None):
    """Saves a permanent record of an agent's action to Postgres."""
    trace = TaskTrace(
        run_id=run_id,
        trace_id=trace_id,
        agent_name=agent_name,
        action=action,
        status=status,
        logs=logs
    )
    db.add(trace)
    await db.commit()

async def hardware_poller():
    """Polls Aethelgard (Rust) and broadcasts to UI via WebSockets."""
    AETHELGARD_HOST = os.getenv("AETHELGARD_HOST", "127.0.0.1")
    AETHELGARD_URL = f"http://{AETHELGARD_HOST}:8003/metrics"

    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(AETHELGARD_URL, timeout=0.5)
                if resp.status_code == 200:
                    metrics = resp.json()
                    await manager.broadcast({"type": "telemetry", "payload": metrics})
            except Exception: # nosec B110
                pass
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(hardware_poller())
    print("[MANAGER] WebSocket bridge initialized.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[WS] UI Client Disconnected.")

# --- THE SWARM RUNNER ---
async def execute_assembly_line(prompt: str):
    """Executes the AI Swarm and saves the state to Postgres."""

    # [DB] Open the database session
    async with AsyncSessionLocal() as db:
        # 1. Create the Genesis Record
        run = SwarmRun(prompt=prompt, status="RUNNING")
        db.add(run)
        await db.commit()
        run_id = run.id

        await manager.broadcast({
            "type": "agent_trace",
            "payload": {"trace_id": "SYS-001", "agent": "Manager", "action": f"Initiating Assembly Line...", "status": "running"}
        })
        await log_trace(db, run_id, "SYS-001", "Manager", f"Initiating Assembly Line for: {prompt}", "success")

        # 2. The Architect
        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "ARCH-001", "agent": "Architect", "action": "Designing system blueprints...", "status": "running"}})

        architect = Architect()
        plan = await asyncio.to_thread(architect.draft_plan, prompt)

        if not plan or 'files' not in plan or len(plan['files']) == 0:
            err_msg = "Architect failed to generate blueprint."
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-ERR", "agent": "System", "action": err_msg, "status": "error"}})
            await log_trace(db, run_id, "SYS-ERR", "System", err_msg, "error")

            run.status = "FAILED"
            await db.commit()
            return

        target_file = plan['files'][0]
        filename = target_file['filename']

        await log_trace(db, run_id, "ARCH-001", "Architect", f"Blueprint drafted for {filename}", "success", json.dumps(plan))

        await manager.broadcast({
            "type": "ast_map",
            "payload": {"nodes": [{"id": filename, "group": "python", "churn_score": 1}], "edges": []}
        })

        # --- THE SELF-HEALING LOOP ---
        MAX_RETRIES = 3
        attempt = 1
        feedback = None

        while attempt <= MAX_RETRIES:
            action_msg = f"Writing implementation for {filename}..." if attempt == 1 else f"Fixing errors in {filename} (Attempt {attempt})..."
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"CODE-00{attempt}", "agent": "Coder", "action": action_msg, "status": "running"}})

            coder = MainCoder()
            file_path = await asyncio.to_thread(coder.write_module, plan, target_file, feedback, attempt)
            await log_trace(db, run_id, f"CODE-00{attempt}", "Coder", action_msg, "success", f"Generated: {file_path}")

            # 3. The Tester
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"TEST-00{attempt}", "agent": "Tester", "action": f"Writing adversarial tests (Attempt {attempt})...", "status": "running"}})
            tester = Tester()
            test_file_path = await asyncio.to_thread(tester.write_tests, filename, feedback, attempt)

            if not test_file_path:
                feedback = "TESTER AGENT FAILED TO GENERATE VALID JSON. Ensure your output is strictly formatted JSON."
                await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{attempt}", "agent": "Manager", "action": "Tester invalid syntax. Retrying...", "status": "error"}})
                await log_trace(db, run_id, f"TEST-00{attempt}", "Tester", "Syntax Error in LLM Output", "error", feedback)
                attempt += 1
                continue

            await log_trace(db, run_id, f"TEST-00{attempt}", "Tester", "Adversarial tests written.", "success", f"Generated: {test_file_path}")

            # 4. The Analyzer
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"ANAL-00{attempt}", "agent": "Analyzer", "action": "Evaluating in Oubliette Sandbox...", "status": "running"}})
            analyzer = Analyzer()
            test_filename = os.path.basename(test_file_path)
            report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

            if report.get("status") == "pass":
                await log_trace(db, run_id, f"ANAL-00{attempt}", "Analyzer", "Sandbox execution passed.", "success", str(report))

                # 5. The Deployer
                await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "DEP-001", "agent": "Deployer", "action": f"Migrating {filename} to production...", "status": "running"}})
                deployer = Deployer()
                prod_path = await asyncio.to_thread(deployer.deploy_module, filename)

                await log_trace(db, run_id, "DEP-001", "Deployer", "Migration complete.", "success", prod_path)

                await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-002", "agent": "Manager", "action": f"Assembly Line Complete. {filename} is live.", "status": "running"}})
                await manager.broadcast({"type": "ast_map", "payload": {"nodes": [{"id": filename, "group": "python", "churn_score": 0}], "edges": []}})

                run.status = "COMPLETED"
                await db.commit()
                break
            else:
                feedback = report.get("logs", "Unknown Execution Error")
                await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{attempt}", "agent": "Manager", "action": "Sandbox rejected code. Extracting logs...", "status": "error"}})
                await log_trace(db, run_id, f"ANAL-00{attempt}", "Analyzer", "Sandbox execution failed.", "error", feedback)
                attempt += 1

        if attempt > MAX_RETRIES:
            run.status = "NEEDS_INTERVENTION"
            await db.commit()

            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-003", "agent": "Manager", "action": "MAX RETRIES EXCEEDED. Escalating to Human-in-the-Loop.", "status": "error"}})
            await log_trace(db, run_id, "SYS-003", "Manager", "Escalating to HITL", "error")

            await manager.broadcast({
                "type": "hitl_alert",
                "payload": {
                    "trace_id": "SYS-001",
                    "filename": filename,
                    "attempt": MAX_RETRIES,
                    "error_traceback": feedback[-500:] if feedback else "Unknown systemic failure.",
                    "action_required": "Provide a hint to fix this or press Quarantine.",
                    "run_id": str(run_id) # Pass DB run_id to frontend
                }
            })

# --- THE NEURAL OVERRIDE (HITL RECOVERY) ---
async def execute_recovery_line(filename: str, hint: str, error_log: str, run_id_str: str):
    async with AsyncSessionLocal() as db:
        # Re-attach to the existing run
        try:
            run_id = uuid.UUID(run_id_str)
        except:
            run_id = None

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-HITL", "agent": "Manager", "action": f"Neural Override Accepted for {filename}. Re-engaging...", "status": "running"}})
        if run_id: await log_trace(db, run_id, "SYS-HITL", "Manager", f"Neural Override: {hint}", "success")

        plan = {"project_name": "Recovery_Protocol", "files": [{"filename": filename, "purpose": "Apply human fix", "signatures": []}]}
        target_file = plan["files"][0]
        feedback_payload = f"PREVIOUS ERROR:\n{error_log}\n\nLEAD ENGINEER OVERRIDE (CRITICAL HINT):\n{hint}"

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "CODE-REC", "agent": "Coder", "action": "Applying human fix...", "status": "running"}})
        coder = MainCoder()
        file_path = await asyncio.to_thread(coder.write_module, plan, target_file, feedback_payload, 4)
        if run_id: await log_trace(db, run_id, "CODE-REC", "Coder", "Human fix applied", "success")

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "TEST-REC", "agent": "Tester", "action": "Validating human fix...", "status": "running"}})
        tester = Tester()
        test_file_path = await asyncio.to_thread(tester.write_tests, filename, "Ensure tests accommodate logic changes.", 4)

        if not test_file_path:
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-HITL-FAIL", "agent": "Manager", "action": "Recovery Tester produced invalid JSON.", "status": "error"}})
            if run_id: await log_trace(db, run_id, "TEST-REC", "Tester", "Invalid JSON", "error")
            return

        await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "ANAL-REC", "agent": "Analyzer", "action": "Evaluating fixed code in Sandbox...", "status": "running"}})
        analyzer = Analyzer()
        test_filename = os.path.basename(test_file_path)
        report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

        if report.get("status") == "pass":
            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "DEP-001", "agent": "Deployer", "action": f"Migrating {filename} to production...", "status": "running"}})
            deployer = Deployer()
            prod_path = await asyncio.to_thread(deployer.deploy_module, filename)

            if run_id:
                await log_trace(db, run_id, "ANAL-REC", "Analyzer", "Recovery Sandbox execution passed.", "success")
                await log_trace(db, run_id, "DEP-001", "Deployer", "Recovery Migration complete.", "success", prod_path)

                # Mark run as recovered and complete
                db_run = await db.get(SwarmRun, run_id)
                if db_run:
                    db_run.status = "COMPLETED_VIA_HITL"
                    await db.commit()

            await manager.broadcast({"type": "agent_trace", "payload": {"trace_id": "SYS-002", "agent": "Manager", "action": f"Assembly Line Complete. {filename} is live.", "status": "running"}})
            await manager.broadcast({"type": "ast_map", "payload": {"nodes": [{"id": filename, "group": "python", "churn_score": 0}], "edges": []}})
        else:
            if run_id: await log_trace(db, run_id, "ANAL-REC", "Analyzer", "Recovery Sandbox failed.", "error", report.get("logs", ""))

            await manager.broadcast({
                "type": "hitl_alert",
                "payload": {
                    "trace_id": "SYS-HITL-FAIL",
                    "filename": filename,
                    "attempt": "RECOVERY",
                    "error_traceback": report.get("logs", "")[-500:],
                    "action_required": "Recovery failed. Provide another hint.",
                    "run_id": run_id_str
                }
            })

@app.post("/build")
async def start_build(intent: dict, background_tasks: BackgroundTasks):
    prompt = intent.get("prompt", "No prompt provided.")
    background_tasks.add_task(execute_assembly_line, prompt)
    return {"status": "Assembly Line Queued"}

@app.post("/hitl/resolve")
async def resolve_hitl(intent: dict, background_tasks: BackgroundTasks):
    filename = intent.get("filename")
    hint = intent.get("hint")
    error_log = intent.get("error_traceback")
    run_id = intent.get("run_id", "")

    background_tasks.add_task(execute_recovery_line, filename, hint, error_log, run_id)
    return {"status": "Recovery Swarm Deployed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
