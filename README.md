<div align="center">

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232b.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

</div>

---

# DEAN-OS v3.0: Distributed Autonomous Engineering Network


## 🚀 The Senior-Grade Agentic Hypervisor


DEAN-OS is an enterprise-grade, local-first orchestration system designed to automate backend software engineering. It bridges the gap between raw LLM inference and deterministic production code through a hardware-locked, zero-trust hypervisor.


This project serves as a comprehensive technical portfolio, demonstrating mastery in **Distributed Systems, Systems Programming (Rust/Python), Cybersecurity, and AI Model Governance.**


---


## 📚 The Technical Dossier (Deep Dives)


To understand the full engineering depth of this system, please review the four core pillars of the DEAN-OS architecture:


1. [**ARCHITECTURE.md**](./docs/ARCHITECTURE.md) – The evolutionary lifecycle from a local prototype to a Dockerized, ACID-compliant microservice cluster.


2. [**SECURITY_MANIFESTO.md**](./docs/SECURITY_MANIFESTO.md) – Zero-Knowledge AES-256 Vaults, Egress Scrubbing, and the "Oubliette" Execution Sandbox.


3. [**OBSERVABILITY.md**](./docs/OBSERVABILITY.md) – Real-time Hardware Telemetry, Distributed Tracing (W3C), and the Mission Control HUD.


4. [**AGENT_GOVERNANCE.md**](./docs/AGENT_GOVERNANCE.md) – Deterministic Plan-Execute-Verify loops and Cognitive Scaling protocols.


---


## 🛠️ Core Engineering Features


* **Hardware-Aware Sentinel (Rust):** Aethelgard monitors VRAM/CPU/RAM in real-time, executing high-priority SIGKILLs to prevent AI-driven hardware exhaustion.


* **Zero-Knowledge Vault (Rust):** Military-grade AES-256-GCM encryption for API keys. Secrets are sealed instantly; plaintext never touches the disk or logs.


* **The Assembly Line Swarm:** A 5-agent team (Architect, Coder, Tester, Analyzer, Deployer) that automates the full CI/CD lifecycle using a Redis-backed task queue.


* **Oubliette Sandbox:** A fully air-gapped, Docker-in-Docker environment where the swarm writes and adversarialy tests its own code without host risk.


* **FinOps Circuit Breaker:** A hardcoded financial governor that violently terminates agentic loops if token usage exceeds a user-defined USD threshold (e.g., $0.01).


---


## 📊 System Visuals


### Mission Control Dashboard
(Insert your Screenshot of the Neon HUD here)


### The Secure Vault & FinOps Governor
(Insert your Screenshot of the Settings Page here)


---


## ⚡ Quickstart


DEAN-OS is fully containerized for reproducible execution.


1. **Initialize Environment:**
   `cp .env.example .env`


2. **Boot the Cluster:**
   `docker-compose up --build -d`


3. **Access the HUD:**
   Navigate to `http://localhost:5173`


---


## 🧪 Verification Matrix


DEAN-OS is built on a "Never Trust, Always Verify" framework. Every module is subjected to adversarial `pytest` suites within the Oubliette sandbox. Only code that passes 100% of functional and security tests is ever migrated to the production `/workspace`.
