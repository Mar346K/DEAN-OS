import asyncio
import json
import os
import sys
import uuid
import ast
import shutil
import re
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
from agents.librarian import Librarian  # <--- IMPORT LIBRARIAN FOR MEMORY LOOP
from tools.ast_surgeon import ASTSurgeon
from sycophant.tools.security import redact_sensitive_info

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import SwarmRun, TaskTrace

# 1. Initialize the Celery App connected to Redis
is_local = os.getenv("REDIS_HOST") is None
redis_host = "127.0.0.1" if is_local else os.getenv("REDIS_HOST")
redis_port = 6380 if is_local else 6379

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{redis_host}:{redis_port}/0")
celery_app = Celery("swarm_tasks", broker=CELERY_BROKER_URL)

# 2. Initialize the Redis Client for Pub/Sub Broadcasting
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# --- SECURITY: LOG REDACTOR ---

def broadcast_to_ui(message: dict):
    """Scrubs and publishes messages to the UI WebSocket."""
    raw_payload = json.dumps(message)
    scrubbed_payload = redact_sensitive_info(raw_payload)
    redis_client.publish("ui_broadcasts", scrubbed_payload)

async def log_trace(db: AsyncSession, run_id: uuid.UUID, trace_id: str, agent_name: str, action: str, status: str, logs: str = None):
    """Scrubs and saves a trace to the persistent PostgreSQL database."""
    safe_action = redact_sensitive_info(action)
    safe_logs = redact_sensitive_info(logs) if logs else None

    trace = TaskTrace(run_id=run_id, trace_id=trace_id, agent_name=agent_name, action=safe_action, status=status, logs=safe_logs)
    db.add(trace)
    await db.commit()

# --- ORCHESTRATION HELPERS ---

def _create_hollow_files(workspace_dir: str, blueprint: dict):
    """Physically creates the files on disk with empty function signatures."""
    print("[ORCHESTRATOR] 🧱 Building Hollow File Skeleton...")
    for node in blueprint.get("nodes", []):
        filepath = os.path.join(workspace_dir, node["filename"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        content = ""
        for sig in node.get("signatures", []):
            content += f"{sig}\n    pass\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

# --- THE V6.0 FSM ORCHESTRATOR (3-TIER PIPELINE + MEMORY LOOP) ---

async def async_execute_assembly_line(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000", rush_mode: bool = False):
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

            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-001", "agent": "Manager", "action": f"Initiating v6.0 Assembly Line...", "status": "running"}})
            await log_trace(db, run_id, "SYS-001", "Manager", f"Initiating Assembly Line for: {prompt}", "success")

            # --- PHASE 1: CLOUD RESEARCH ---
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "RES-001", "agent": "Researcher", "action": "Querying for Technical Brief...", "status": "running"}})
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

            # --- PHASE 3: HOLLOW BUILD (STAGING) ---
            workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../../staging/projects/{p_tag}/workspace"))
            os.makedirs(workspace_dir, exist_ok=True)
            _create_hollow_files(workspace_dir, blueprint)

            ui_nodes = [{"id": n["filename"], "group": "python", "churn_score": 1} for n in blueprint.get("nodes", [])]
            ui_edges = blueprint.get("edges", [])
            broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})

            # --- PHASE 4: ATOMIC NODE EXECUTION (THE FSM LOOP) ---
            surgeon = ASTSurgeon()
            librarian = Librarian(project_id=p_tag)  # Initialize the Memory Engine

            for idx, node in enumerate(blueprint.get("nodes", [])):
                filename = node["filename"]
                ui_nodes[idx]["churn_score"] = 5
                broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})

                MAX_RETRIES = 2
                attempt = 1
                feedback = None
                cumulative_errors = "" # Track all errors for this node to feed to the Librarian

                while attempt <= MAX_RETRIES:
                    action_msg = f"Atomic Coder targeting {filename}..." if attempt == 1 else f"Fixing errors in {filename} (Attempt {attempt})..."
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"CODE-{idx}-{attempt}", "agent": "Coder", "action": action_msg, "status": "running"}})

                    coder = MainCoder(project_id=p_tag)
                    raw_file_path = await asyncio.to_thread(coder.write_module, blueprint, node, feedback, attempt)

                    if not raw_file_path:
                        feedback = "Failed to extract Python from Markdown."
                        cumulative_errors += f"Attempt {attempt}: {feedback}\n"
                        attempt += 1
                        continue

                    # AST Surgeon (Structural & Security Compliance)
                    try:
                        with open(raw_file_path, "r", encoding="utf-8") as f:
                            raw_code = f.read()
                        healed_code = surgeon.enforce_contract(raw_code, node)
                        with open(raw_file_path, "w", encoding="utf-8") as f:
                            f.write(healed_code)
                        await log_trace(db, run_id, f"CODE-{idx}-{attempt}", "AST Surgeon", f"Syntax enforced on {filename}", "success")
                    except Exception as e:
                        feedback = f"AST SURGEON REJECTED CODE: {e}"
                        cumulative_errors += f"Attempt {attempt}: {feedback}\n"
                        attempt += 1
                        continue

                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"TEST-{idx}-{attempt}", "agent": "Tester", "action": f"Testing {filename}...", "status": "running"}})
                    tester = Tester(project_id=p_tag)
                    test_file_path = await asyncio.to_thread(tester.write_tests, filename, feedback, attempt)

                    if not test_file_path:
                        feedback = "Failed to generate tests."
                        cumulative_errors += f"Attempt {attempt}: {feedback}\n"
                        attempt += 1
                        continue

                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"ANAL-{idx}-{attempt}", "agent": "Analyzer", "action": "Oubliette Sandbox Verification...", "status": "running"}})
                    analyzer = Analyzer(project_id=p_tag)
                    test_filename = os.path.basename(test_file_path)
                    report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

                    if report.get("status") == "pass":
                        await log_trace(db, run_id, f"ANAL-{idx}-{attempt}", "Analyzer", "Sandbox passed.", "success", str(report))

                        # --- PHASE 12: THE MEMORY LOOP ---
                        # If the Swarm failed initially but figured it out, save the lesson to global memory
                        if attempt > 1 and cumulative_errors:
                            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"MEM-{idx}", "agent": "Librarian", "action": "Extracting Lesson Learned...", "status": "running"}})
                            await asyncio.to_thread(librarian.summarize_fix, filename, cumulative_errors, healed_code)

                        # --- PHASE 4e. PROMOTION TO RELEASE VAULT ---
                        try:
                            docker_workspace_dir = f"/app/staging/projects/{p_tag}/workspace"
                            docker_vault_dir = f"/app/staging/projects/{p_tag}/release_vault"
                            os.makedirs(docker_vault_dir, exist_ok=True)

                            source_file = os.path.join(docker_workspace_dir, filename)
                            dest_file = os.path.join(docker_vault_dir, filename)

                            shutil.copyfile(source_file, dest_file)
                            os.remove(source_file)

                            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"DEP-{idx}", "agent": "Orchestrator", "action": f"Module {filename} verified and promoted to Release Vault.", "status": "success"}})
                            ui_nodes[idx]["churn_score"] = 0
                            broadcast_to_ui({"type": "ast_map", "payload": {"nodes": ui_nodes, "edges": ui_edges}})
                            break
                        except Exception as promotion_error:
                            err_msg = f"Failed to move {filename} to Vault: {str(promotion_error)}"
                            await log_trace(db, run_id, f"SYS-ERR-{idx}", "Orchestrator", "Promotion Failed", "error", err_msg)
                            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{idx}", "agent": "Orchestrator", "action": err_msg, "status": "error"}})
                            break
                    else:
                        feedback = report.get("logs", "Execution Error")
                        cumulative_errors += f"Attempt {attempt} Sandbox Error:\n{feedback}\n"
                        await log_trace(db, run_id, f"ANAL-{idx}-{attempt}", "Analyzer", "Sandbox failed.", "error", feedback)
                        attempt += 1

                if attempt > MAX_RETRIES:
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{idx}", "agent": "Manager", "action": f"Node {filename} FAILED. Halting Pipeline.", "status": "error"}})
                    run.status = "NEEDS_INTERVENTION"
                    await db.commit()

                    broadcast_to_ui({
                        "type": "hitl_alert",
                        "payload": {
                            "trace_id": f"SYS-ERR-{idx}",
                            "filename": filename,
                            "attempt": MAX_RETRIES,
                            "error_traceback": feedback[-500:] if feedback else "Unknown failure.",
                            "action_required": "Fix module to resume.",
                            "run_id": str(run_id)
                        }
                    })
                    return

            run.status = "COMPLETED"
            await db.commit()
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-999", "agent": "Manager", "action": "All Modules Verified. Release Vault Populated.", "status": "success"}})

        finally:
            await engine.dispose()

# --- THE NEW ASYNC INGESTION WORKER ---
@celery_app.task(name="sycophant.tasks.process_ingestion")
def process_ingestion_task(safe_filename: str, project_id_str: str = "default"):
    """
    Runs completely decoupled from the Web Server.
    Handles extraction, junk scrubbing, and Librarian neural zipping.
    """
    import httpx

    workspace_dir = f"/app/staging/projects/{project_id_str}/workspace"
    oubliette_host = os.getenv("OUBLIETTE_HOST", "oubliette")
    secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

    import valkyrie_crypto
    token = valkyrie_crypto.forge_token("worker-forge", "analyzer", secret)

    # 1. Ask Oubliette to safely extract it
    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-1", "agent": "Manager", "action": f"Requesting secure extraction of {safe_filename}...", "status": "running"}})
    try:
        # Note: We must use a synchronous httpx client here because we are outside an async function
        with httpx.Client() as client:
            client.post(f"http://{oubliette_host}:8002/extract", json={"filename": safe_filename, "project_id": project_id_str}, headers={"Authorization": f"Bearer {token}"}, timeout=120.0)
    except Exception as e:
        broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-ERR", "agent": "Manager", "action": f"Extraction failed: {e}", "status": "error"}})
        return

    # 2. Cleanup the original zip
    file_path = os.path.join(workspace_dir, safe_filename)
    if os.path.exists(file_path):
        try: os.remove(file_path)
        except OSError: pass

    # 3. Scrub Junk (We must define the local scrub logic here)
    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-2", "agent": "Manager", "action": "Scrubbing virtual environments and __pycache__...", "status": "running"}})
    junk_names = {'.venv', 'venv', '__pycache__', 'node_modules', '.pytest_cache', '.git'}
    for root, dirs, files in os.walk(workspace_dir, topdown=False):
        for name in dirs:
            if name in junk_names:
                junk_path = os.path.join(root, name)
                try: shutil.rmtree(junk_path)
                except Exception: pass # nosec B110

    # 4. Neural Zip via Librarian
    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-3", "agent": "Librarian", "action": "Initiating Neural Zip vectorization...", "status": "running"}})
    try:
        librarian = Librarian(project_id=project_id_str)
        # Librarian is synchronous, so we just call it directly
        librarian.process_workspace(workspace_dir)
        broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-4", "agent": "Librarian", "action": "Neural Zip complete. Workspace mapped to Mnemosyne.", "status": "success"}})

        # We broadcast a special signal that the UI can listen for to trigger a fetchWorkspace()
        broadcast_to_ui({"type": "ingest_complete", "payload": {}})
    except Exception as e:
        broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "INGEST-ERR", "agent": "Librarian", "action": f"Vectorization failed: {e}", "status": "error"}})

# --- EXISTING ASSEMBY LINE TASK ---
@celery_app.task(name="sycophant.tasks.execute_assembly_line")
def execute_assembly_line_task(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000", rush_mode: bool = False):
    asyncio.run(async_execute_assembly_line(prompt, project_id_str, rush_mode))
