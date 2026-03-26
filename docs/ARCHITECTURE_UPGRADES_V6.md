# DEAN-OS Architecture Upgrades V6: The Command Center

## Overview
This document outlines the transition of the DEAN-OS React frontend from a single-pane dashboard into a multi-tab Command Center. It also establishes the backend security protocols for Hybrid-Cloud execution and zero-trust legacy code ingestion.

---

## Phase 1: The Shell & The Forensic Ledger
**Objective:** Establish the new UI architecture and expose the AI's permanent memory without compromising host security.
* **The Command Shell:** Implement a state-based top navigation bar in React featuring tabs: `AST Mapper`, `Staging`, `Workspace`, `Logs`, and `Settings`.
* **The Forensic Ledger (Logs Tab):** * *Security Note:* Direct Docker socket access from the browser is prohibited.
    * *Implementation:* Create a new FastAPI endpoint (`GET /logs`) that queries the `task_traces` table in Postgres. The UI will display this as a searchable, scrolling terminal, giving full historical visibility into the Swarm's actions.

## Phase 2: The Workspace & The Intake Forge
**Objective:** Provide visual access to deployed modules and establish a secure pipeline for ingesting legacy codebases.
* **Workspace Viewer:** A File Tree component in the React UI that reads the backend `/workspace` directory, allowing users to view deployed Python files and export/download the project.
* **The Intake Forge (ZIP Dropzone):**
    * *UI:* A drag-and-drop zone in the Workspace tab for `.zip` files.
    * *Security Pipeline:* The ZIP is streamed to the `deanos_oubliette` sandbox. Oubliette extracts the files in an air-gapped container to neutralize path-traversal attacks.
    * *The Bloom:* Once extracted safely, Mnemosyne vectorizes the code and automatically triggers a broadcast to update the AST ReactFlow graph.

## Phase 3: The Staging Ground
**Objective:** Real-time visibility into the active assembly line.
* **Live Telemetry:** A dedicated UI tab that monitors the `/staging` directory.
* **Feature:** Allows the user to visually watch the code being generated and tested in real-time as the Coder and Tester agents iterate, providing a deeper look than the standard waterfall trace.

## Phase 4: The Cloud Gate & Vault Settings
**Objective:** Enable Hybrid-Cloud execution (Claude/Gemini) while maintaining strict data sovereignty and local encryption.
* **The Vault (Settings Tab):** UI controls to toggle between Strict Local, Hybrid, and Full Cloud modes. Includes secure, masked inputs for external API keys and controls to wipe system memory (Qdrant/Postgres).
* **Valkyrie Crypto Engine (Rust):** API keys are never saved as plaintext. The Rust service will handle AES-256 encryption using a local master key before storing external keys in Postgres.
* **The Egress Guard (Python):** A regex-based scrubber middleware that anonymizes proprietary variables and IP addresses before routing high-complexity reasoning tasks to external Cloud APIs.
