import asyncio
import json
import os
import sys
import uuid
from celery import Celery
import redis

# Ensure we can import our agents and database
sys.path.append(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer

# Import the necessary SQLAlchemy tools directly
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import SwarmRun, TaskTrace

# 1. Initialize the Celery App connected to Redis
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("swarm_tasks", broker=CELERY_BROKER_URL)

# 2. Initialize the Redis Client for Pub/Sub Broadcasting
redis_host = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def broadcast_to_ui(message: dict):
    """Publishes a message to Redis so the Web Server can forward it to WebSockets."""
    redis_client.publish("ui_broadcasts", json.dumps(message))

async def log_trace(db: AsyncSession, run_id: uuid.UUID, trace_id: str, agent_name: str, action: str, status: str, logs: str = None):
    """Saves a permanent record of an agent's action to Postgres."""
    trace = TaskTrace(
        run_id=run_id, trace_id=trace_id, agent_name=agent_name,
        action=action, status=status, logs=logs
    )
    db.add(trace)
    await db.commit()

# --- THE ASYNC WORKER LOGIC ---
async def async_execute_assembly_line(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000"):
    # CRITICAL FIX: Create the DB engine INSIDE the async loop so it's tied to this specific thread's event loop
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://deanos_admin:deanos_vault_2026@db/deanos_history")
    engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        try:
            # Convert string ID to UUID object, handling backwards compatibility
            pid = uuid.UUID(project_id_str) if project_id_str != "00000000-0000-0000-0000-000000000000" else None

            run = SwarmRun(prompt=prompt, status="RUNNING", project_id=pid)
            db.add(run)
            await db.commit()
            run_id = run.id

            # Project Tag ensures agents have a folder even if the DB row isn't formally assigned yet
            p_tag = str(pid) if pid else "default"

            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-001", "agent": "Manager", "action": f"Initiating Assembly Line...", "status": "running"}})
            await log_trace(db, run_id, "SYS-001", "Manager", f"Initiating Assembly Line for: {prompt}", "success")

            # 1. Architect
            broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "ARCH-001", "agent": "Architect", "action": "Designing system blueprints...", "status": "running"}})
            architect = Architect(project_id=p_tag)
            plan = await asyncio.to_thread(architect.draft_plan, prompt)

            if not plan or 'files' not in plan or len(plan['files']) == 0:
                err_msg = "Architect failed to generate blueprint."
                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-ERR", "agent": "System", "action": err_msg, "status": "error"}})
                await log_trace(db, run_id, "SYS-ERR", "System", err_msg, "error")
                run.status = "FAILED"
                await db.commit()
                return

            target_file = plan['files'][0]
            filename = target_file['filename']
            await log_trace(db, run_id, "ARCH-001", "Architect", f"Blueprint drafted for {filename}", "success", json.dumps(plan))
            broadcast_to_ui({"type": "ast_map", "payload": {"nodes": [{"id": filename, "group": "python", "churn_score": 1}], "edges": []}})

            MAX_RETRIES = 3
            attempt = 1
            feedback = None

            while attempt <= MAX_RETRIES:
                action_msg = f"Writing implementation for {filename}..." if attempt == 1 else f"Fixing errors in {filename} (Attempt {attempt})..."
                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"CODE-00{attempt}", "agent": "Coder", "action": action_msg, "status": "running"}})

                coder = MainCoder(project_id=p_tag)
                file_path = await asyncio.to_thread(coder.write_module, plan, target_file, feedback, attempt)
                await log_trace(db, run_id, f"CODE-00{attempt}", "Coder", action_msg, "success", f"Generated: {file_path}")

                # 2. Tester
                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"TEST-00{attempt}", "agent": "Tester", "action": f"Writing adversarial tests (Attempt {attempt})...", "status": "running"}})
                tester = Tester(project_id=p_tag)
                test_file_path = await asyncio.to_thread(tester.write_tests, filename, feedback, attempt)

                if not test_file_path:
                    feedback = "TESTER AGENT FAILED TO GENERATE VALID JSON."
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{attempt}", "agent": "Manager", "action": "Tester invalid syntax. Retrying...", "status": "error"}})
                    await log_trace(db, run_id, f"TEST-00{attempt}", "Tester", "Syntax Error in LLM Output", "error", feedback)
                    attempt += 1
                    continue

                await log_trace(db, run_id, f"TEST-00{attempt}", "Tester", "Adversarial tests written.", "success", f"Generated: {test_file_path}")

                # 3. Analyzer
                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"ANAL-00{attempt}", "agent": "Analyzer", "action": "Evaluating in Oubliette Sandbox...", "status": "running"}})
                analyzer = Analyzer(project_id=p_tag)
                test_filename = os.path.basename(test_file_path)
                report = await asyncio.to_thread(analyzer.evaluate_code, test_filename)

                if report.get("status") == "pass":
                    await log_trace(db, run_id, f"ANAL-00{attempt}", "Analyzer", "Sandbox execution passed.", "success", str(report))

                    # 4. Deployer
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "DEP-001", "agent": "Deployer", "action": f"Migrating {filename} to production...", "status": "running"}})
                    deployer = Deployer(project_id=p_tag)
                    prod_path = await asyncio.to_thread(deployer.deploy_module, filename)

                    await log_trace(db, run_id, "DEP-001", "Deployer", "Migration complete.", "success", prod_path)
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-002", "agent": "Manager", "action": f"Assembly Line Complete. {filename} is live.", "status": "running"}})
                    broadcast_to_ui({"type": "ast_map", "payload": {"nodes": [{"id": filename, "group": "python", "churn_score": 0}], "edges": []}})

                    run.status = "COMPLETED"
                    await db.commit()
                    break
                else:
                    feedback = report.get("logs", "Unknown Execution Error")
                    broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": f"SYS-ERR-{attempt}", "agent": "Manager", "action": "Sandbox rejected code. Extracting logs...", "status": "error"}})
                    await log_trace(db, run_id, f"ANAL-00{attempt}", "Analyzer", "Sandbox execution failed.", "error", feedback)
                    attempt += 1

            if attempt > MAX_RETRIES:
                run.status = "NEEDS_INTERVENTION"
                await db.commit()

                broadcast_to_ui({"type": "agent_trace", "payload": {"trace_id": "SYS-003", "agent": "Manager", "action": "MAX RETRIES EXCEEDED. Escalating to Human-in-the-Loop.", "status": "error"}})
                await log_trace(db, run_id, "SYS-003", "Manager", "Escalating to HITL", "error")

                broadcast_to_ui({
                    "type": "hitl_alert",
                    "payload": {
                        "trace_id": "SYS-001",
                        "filename": filename,
                        "attempt": MAX_RETRIES,
                        "error_traceback": feedback[-500:] if feedback else "Unknown systemic failure.",
                        "action_required": "Provide a hint to fix this or press Quarantine.",
                        "run_id": str(run_id)
                    }
                })
        finally:
            await engine.dispose() # Cleanly close the DB connection pool for this run

# --- CELERY ENTRY POINTS ---
@celery_app.task(name="sycophant.tasks.execute_assembly_line")
def execute_assembly_line_task(prompt: str, project_id_str: str = "00000000-0000-0000-0000-000000000000"):
    asyncio.run(async_execute_assembly_line(prompt, project_id_str))
