import asyncio
import json
import os
import sys
import uuid
import ast
from celery import Celery
import redis

# Ensure we can import our agents and database
sys.path.append(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.researcher import CloudResearcher
from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer
from tools.ast_surgeon import ASTSurgeon

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import SwarmRun, TaskTrace

# 1. Initialize the Celery App connected to Redis
# If running on Windows, use 6380. If inside Docker, it will use the env var.
is_local = os.getenv("REDIS_HOST") is None
redis_host = "127.0.0.1" if is_local else os.getenv("REDIS_HOST")
redis_port = 6380 if is_local else 6379

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{redis_host}:{redis_port}/0")
celery_app = Celery("swarm_tasks", broker=CELERY_BROKER_URL)

# 2. Initialize the Redis Client for Pub/Sub Broadcasting
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

def broadcast_to_ui(message: dict):
    redis_client.publish("ui_broadcasts", json.dumps(message))

async def log_trace(db: AsyncSession, run_id: uuid.UUID, trace_id: str, agent_name: str, action: str, status: str, logs: str = None):
    trace = TaskTrace(run_id=run_id, trace_id=trace_id, agent_name=agent_name, action=action, status=status, logs=logs)
    db.add(trace)
    await db.commit()

def _create_hollow_files(workspace_dir: str, blueprint: dict):
    """
    Physically creates the files on disk with empty function signatures (The Contract)
    before the Coder ever touches them.
    """
    print("[ORCHESTRATOR] 🧱 Building Hollow File Skeleton...")
    for node in blueprint.get("nodes", []):
        filepath = os.path.join(workspace_dir, node["filename"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        content = ""
        for sig in node.get("signatures", []):
            content += f"{sig}\n    pass\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

# --- THE V5.0 FSM ORCHESTRATOR ---
async def async_execute_assembly_line(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000"):
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://deanos_admin:deanos_vault_2026@db/deanos_history")
    engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        try:
            pid = uuid.UUID(project_id_str) if project_id_str != "00000000-0000-0000-0000-000000000000" else None
            run = SwarmRun(prompt=prompt, status="RUNNING", project_id=pid)
            db.add(run)
            await db.commit()
            run_id = run.id
            p_tag = str(pid) if pid else "default"

            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-001", "agent": "Manager", "action": f"Initiating Graph-Native Assembly Line...", "status": "running"}})
            await log_trace(db, run_id, "SYS-001", "Manager", f"Initiating Assembly Line for: {prompt}", "success")

            # --- PHASE 1: CLOUD RESEARCH ---
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "RES-001", "agent": "Researcher", "action": "Querying Gemini 2.5 Flash for Technical Brief...", "status": "running"}})
            researcher = CloudResearcher()
            tech_brief = await asyncio.to_thread(researcher.research_task, prompt)
            await log_trace(db, run_id, "RES-001", "Researcher", "Technical Brief Acquired.", "success", tech_brief)

            # --- PHASE 2: GRAPH ARCHITECTURE ---
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "ARCH-001", "agent": "Architect", "action": "Generating DAG Blueprint...", "status": "running"}})
            architect = Architect(project_id=p_tag)
            blueprint = await asyncio.to_thread(architect.draft_plan, prompt, tech_brief)

            if not blueprint:
                err_msg = "Architect failed: Invalid JSON Graph."
                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-ERR", "agent": "System", "action": err_msg, "status": "error"}})
                run.status = "FAILED"
                await db.commit()
                return

            await log_trace(db, run_id, "ARCH-001", "Architect", "DAG Blueprint generated.", "success", json.dumps(blueprint))

            # --- PHASE 3: HOLLOW BUILD ---
            workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../../staging/projects/{p_tag}/workspace"))
            os.makedirs(workspace_dir, exist_ok=True)
            _create_hollow_files(workspace_dir, blueprint)

            # Update UI with the full graph
            ui_nodes = [{"id": n["filename"], "group": "python", "churn_score": 1} for n in blueprint.get("nodes", [])]
            ui_edges = blueprint.get("edges", [])
            broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})

            # --- PHASE 4: ATOMIC NODE EXECUTION (THE FSM LOOP) ---
            surgeon = ASTSurgeon()
            deployer = Deployer(project_id=p_tag)

            for idx, node in enumerate(blueprint.get("nodes", [])):
                filename = node["filename"]

                # Update UI to show which node is active
                ui_nodes[idx]["churn_score"] = 5  # Make it pulse in the UI
                broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})

                MAX_RETRIES = 2
                attempt = 1
                feedback = None

                while attempt <= MAX_RETRIES:
                    action_msg = f"Atomic Coder targeting {filename}..." if attempt == 1 else f"Fixing errors in {filename} (Attempt {attempt})..."
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"CODE-{idx}-{attempt}", "agent": "Coder", "action": action_msg, "status": "running"}})

                    # 4a. Write Logic
                    coder = MainCoder(project_id=p_tag)
                    raw_file_path = await asyncio.to_thread(coder.write_module, blueprint, node, feedback, attempt)

                    if not raw_file_path:
                        feedback = "Failed to extract Python from Markdown."
                        attempt += 1
                        continue

                    # 4b. The AST Surgeon Enforces the Contract
                    try:
                        with open(raw_file_path, "r", encoding="utf-8") as f:
                            raw_code = f.read()

                        healed_code = surgeon.enforce_contract(raw_code, node)

                        with open(raw_file_path, "w", encoding="utf-8") as f:
                            f.write(healed_code)

                        await log_trace(db, run_id, f"CODE-{idx}-{attempt}", "AST Surgeon", f"Syntax enforced on {filename}", "success")
                    except Exception as e:
                        feedback = f"AST SURGEON REJECTED CODE: {e}"
                        attempt += 1
                        continue

                    # 4c. Write Tests
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"TEST-{idx}-{attempt}", "agent": "Tester", "action": f"Testing {filename}...", "status": "running"}})
                    tester = Tester(project_id=p_tag)
                    test_file_path = await asyncio.to_thread(tester.write_tests, filename, feedback, attempt)

                    if not test_file_path:
                        feedback = "Failed to generate tests."
                        attempt += 1
                        continue

                    # 4d. Sandbox Evaluation
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"ANAL-{idx}-{attempt}", "agent": "Analyzer", "action": "Oubliette Sandbox Verification...", "status": "running"}})
                    analyzer = Analyzer(project_id=p_tag)
                    test_filename = os.path.basename(test_file_path)
                    report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

                    if report.get("status") == "pass":
                        await log_trace(db, run_id, f"ANAL-{idx}-{attempt}", "Analyzer", "Sandbox passed.", "success", str(report))

                        # 4e. Deploy Node
                        await asyncio.to_thread(deployer.deploy_module, filename)
                        ui_nodes[idx]["churn_score"] = 0 # Mark as verified in UI
                        broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})
                        break # Node complete, move to next node
                    else:
                        feedback = report.get("logs", "Execution Error")
                        await log_trace(db, run_id, f"ANAL-{idx}-{attempt}", "Analyzer", "Sandbox failed.", "error", feedback)
                        attempt += 1

                # Check if the node exhausted its retries
                if attempt > MAX_RETRIES:
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{idx}", "agent": "Manager", "action": f"Node {filename} FAILED. Halting Graph Traversal.", "status": "error"}})
                    run.status = "NEEDS_INTERVENTION"
                    await db.commit()

                    broadcast_to_ui({
                        "type": "hitl_alert",
                        "payload": {
                            "trace_id": f"SYS-ERR-{idx}",
                            "filename": filename,
                            "attempt": MAX_RETRIES,
                            "error_traceback": feedback[-500:] if feedback else "Unknown systemic failure.",
                            "action_required": "Fix this module in the UI editor to resume graph traversal.",
                            "run_id": str(run_id)
                        }
                    })
                    return # Halt the entire pipeline until the human fixes it

            # If the loop finishes naturally, the whole graph is deployed!
            run.status = "COMPLETED"
            await db.commit()
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-999", "agent": "Manager", "action": "All Graph Nodes Compiled and Deployed.", "status": "success"}})

        finally:
            await engine.dispose()

@celery_app.task(name="sycophant.tasks.execute_assembly_line")
def execute_assembly_line_task(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000"):
    asyncio.run(async_execute_assembly_line(prompt, project_id_str))
