# ARCHITECTURE.md: The DEAN-OS Evolution

## 1. Vision & Purpose
**DEAN-OS (Distributed Autonomous Engineering Network)** is a local-first, agentic hypervisor designed to automate backend software engineering. It operates on a "Zero-Trust" principle, treating AI agents as isolated, hostile entities within a controlled environment.

### The Core Problems Solved:
* **Data Sovereignty:** Proprietary code never leaves the local machine.
* **Compute Economics:** Utilizing local edge-computing (Intel Arc A770) to offset cloud API costs.
* **Deterministic Reliability:** Solving LLM hallucination through a hardware-locked Plan-Execute-Verify loop.

---

## 2. The Tech Stack
* **Systems:** Rust (Aethelgard) & Python 3.11 (Sycophant API).
* **Orchestration:** Docker & Docker Compose (Horizontal Scaling).
* **Messaging:** Redis (Message Broker) & WebSockets (Real-time Telemetry).
* **State Management:** PostgreSQL (ACID Audit Logs) & SQLAlchemy.
* **Memory:** Qdrant (Vector DB) & Mnemosyne RAG Engine.
* **Frontend:** React (Vite) with ReactFlow for AST Visualizations.

---

## 3. System Topology

| Service | Responsibility | Logic Layer |
| :--- | :--- | :--- |
| **Aethelgard** | Hardware Sentinel | **Rust:** Monitors VRAM/CPU/RAM and executes SIGKILL on runaway tasks. |
| **Valkyrie** | The Firewall | **Rust:** AES-256-GCM Vault, JWT RBAC, and FinOps budget enforcement. |
| **Sycophant** | The Manager | **Python:** FastAPI bridge between the UI and the Swarm. |
| **Mnemosyne** | Institutional Memory | **Python:** Vectorizes codebases and retrieves [TRUTH_SOURCE] documentation. |
| **Oubliette** | The Proving Ground | **Docker:** Air-gapped sandbox for code execution and adversarial testing. |
| **Redis** | The Nervous System | **Pub/Sub:** Handles distributed state and Celery task dispatching. |

---

## 4. The Evolutionary Lifecycle

### Phase I: Foundations
Transitioned from a "black box" script to a Microservice Architecture. Established the **Resource Governor** to prevent AI-driven OOM crashes and implemented the **Aegis Proxy** to air-gap the agents.

### Phase II: The Assembly Line
Implemented a 5-Agent Production Suite to eliminate hallucination:
1. **Architect:** Drafts JSON blueprints.
2. **Coder:** Implements logic file-by-file.
3. **Tester:** Generates adversarial `pytest` suites.
4. **Analyzer:** Parses `Oubliette` tracebacks to fix bugs.
5. **Deployer:** Validates and migrates code to production.

### Phase III: Intelligence & Observability
* **Symbolic Dependency Mapping:** Using Python AST to map codebases, preventing agents from "guessing" imports.
* **Distributed Tracing:** Every action is stamped with a W3C Trace ID, providing a millisecond-accurate waterfall log.
* **Hybrid-Cloud Routing:** Tiered Router that uses local 8B models for syntax and escalates to Gemini/Claude for high-complexity reasoning.

### Phase IV: Enterprise Hardening
* **ACID Compliance:** Migrated system state to PostgreSQL to ensure every failure and micro-charge is auditable.
* **Zero-Knowledge Vault:** Built a hardware-locked vault using AES-256 encryption for API keys.
* **FinOps Circuit Breaker:** Hard USD budget governor that terminates tasks if token usage exceeds a strict threshold (e.g., $0.01).

---

## 5. Deployment
DEAN-OS is fully containerized. Infrastructure is managed via `docker-compose.yml`, allowing for reproducible environments across Windows (WSL2) and Linux.
