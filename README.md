<div align="center">

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232b.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white)
![Qdrant](https://img.shields.io/badge/qdrant-%23E1523D.svg?style=for-the-badge&logo=qdrant&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

</div>

---

# DEAN-OS v6.0: Distributed Autonomous Engineering Network

## 🚀 The Senior-Grade Agentic Hypervisor

DEAN-OS is an enterprise-grade, local-first orchestration system designed to automate backend software engineering. Evolving from a synchronous prototype into a fully decoupled, asynchronous microservice cluster, it bridges the gap between raw LLM inference and deterministic production code through a hardware-locked, zero-trust hypervisor.

This project serves as a comprehensive technical portfolio, demonstrating mastery in **Distributed Systems, Asynchronous Event-Driven Architecture, Systems Programming (Rust/Python), Cybersecurity, and AI Model Governance.**

---

## 📚 The Technical Dossier (Deep Dives)

To understand the full engineering depth of this system, please review the core pillars of the DEAN-OS architecture:

1. [**ARCHITECTURE.md**](./docs/ARCHITECTURE.md) – The evolutionary lifecycle from a local script to an Asynchronous Celery/Redis cluster with ACID-compliant PostgreSQL telemetry.
2. [**SECURITY_MANIFESTO.md**](./docs/SECURITY_MANIFESTO.md) – Zero-Knowledge AES-256 Vaults, recursive workspace sanitization, and the "Oubliette" Execution Sandbox.
3. [**OBSERVABILITY.md**](./docs/OBSERVABILITY.md) – Real-time Hardware Telemetry, ReactFlow AST Blast-Radius Mapping, and the Mission Control HUD.
4. [**AGENT_GOVERNANCE.md**](./docs/AGENT_GOVERNANCE.md) – Deterministic Plan-Execute-Verify loops, dynamic multi-model routing (Gemini Flash/OpenRouter), and Cognitive Scaling protocols.
5. [**MEMORY_ENGINE.md**](./docs/MEMORY_ENGINE.md) – The Librarian agent, utilizing local `all-MiniLM-L6-v2` embeddings and Qdrant vector databases for permanent "Neural Zip" swarm memory.

---

## 🛠️ Core Engineering Features

* **Asynchronous Ingestion Pipeline:** A fully decoupled Celery/Redis worker daemon that handles heavy file extraction, recursive junk scrubbing (`.venv`, `__pycache__`), and vectorization without blocking the FastAPI web server.
* **Smart Inference Gateway:** A dynamic, fault-tolerant routing switchboard. Heavy data ingestion is automatically routed to Gemini 2.5 Flash for 1M-token context windows, complex logic hits OpenRouter, and it seamlessly falls back to local air-gapped Ollama models if cloud connections fail.
* **The Librarian (RAG Memory Engine):** A dedicated background agent that automatically maps valid workspaces into semantic JSON vectors, storing lessons learned in a Qdrant Vault so the swarm never makes the same mistake twice.
* **Hardware-Aware Sentinel (Rust):** Aethelgard monitors VRAM/CPU/RAM in real-time, executing high-priority SIGKILLs to prevent AI-driven hardware exhaustion.
* **Oubliette Sandbox:** A fully air-gapped, Docker-in-Docker environment where the swarm writes and adversarialy tests its own code. Strict volume mounting prevents path traversal and Zip Slip vulnerabilities.
* **FinOps Circuit Breaker:** A hardcoded financial governor that violently terminates agentic loops if token usage exceeds a user-defined USD threshold.

---

## 🏭 How It Works (For Humans)

If you aren't familiar with distributed asynchronous architecture, imagine DEAN-OS as a highly secure, automated manufacturing plant:

1. **The Intake Desk (API Server):** You drop a ZIP file of code into the dashboard. Instead of making you wait while it opens and reads everything, the receptionist slaps a tracking barcode on it, drops it on a conveyor belt, and immediately lets you get back to work.
2. **The Conveyor Belt (Redis Queue):** If ten people drop off packages at once, they just line up neatly. The system never crashes or gets overwhelmed.
3. **The Hazmat Room (Oubliette Sandbox):** A dedicated factory worker takes the package into a sealed, blast-proof room to open it. If there is a malicious virus inside, it only damages the empty room, keeping the rest of the factory perfectly safe.
4. **The Clean-Up Crew (The Scrub):** The worker aggressively throws away all the useless packing peanuts and generated junk files so the AI doesn't waste time (or money) reading them.
5. **The Grand Library (AI Vector DB):** The clean blueprints are handed to the Librarian agent. The Librarian speed-reads every single page, writes a 1-sentence summary of what it does, translates that summary into math, and files it into an infinite, searchable filing cabinet.
6. **The Pager (WebSocket Broadcast):** The moment the Librarian closes the drawer, a signal flashes back to the front desk, and your screen instantly updates to show the fully unpacked, searchable project.

---

## 📊 System Visuals

### Mission Control & Live Waterfall Trace
*(Insert your Screenshot of the Neon HUD here)*

### AST Forensic Visualizer (Blast Radius)
*(Insert your Screenshot of the ReactFlow AST Node Graph here)*

### The Secure Vault & FinOps Governor
*(Insert your Screenshot of the Settings Page here)*

---

## ⚡ Quickstart

DEAN-OS is fully containerized for reproducible execution across 8 independent microservices.

1. **Initialize Environment:**
   `cp .env.example .env`

2. **Boot the Cluster:**
   `docker-compose up --build -d`

3. **Access the HUD:**
   Navigate to `http://localhost:5173`

---

## 🧪 Verification Matrix

DEAN-OS is built on a "Never Trust, Always Verify" framework. Every module is subjected to adversarial `pytest` suites within the Oubliette sandbox. Only code that passes 100% of functional and security tests is ever migrated to the production `/release_vault`.
