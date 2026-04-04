# DEAN-OS v5.0 Upgrade Plan: The Graph-Native Ecosystem

*Date: April 2, 2026*
*Objective: Scale DEAN-OS from a linear, single-file generator into a highly resilient, 100+ module orchestration engine. Overcome consumer hardware limits (16GB VRAM) by leveraging Cloud API reasoning (Gemini) and deterministic local syntax enforcement (AST).*

---

## 1. Architectural Philosophy

We are abandoning the concept of "LLMs as free-typing programmers." Current LLMs suffer from context degradation and syntax hallucination.

To achieve enterprise-grade reliability, DEAN-OS v5.0 operates on **Contract-Driven Development**:
1. **The Brain (Cloud):** Generates the structure (Nodes/Contracts).
2. **The Physics (Python/Rust):** Generates hollow files and enforces variable naming deterministically.
3. **The Muscle (Local GPU):** Fills in the isolated logic for one node at a time.

---

## 2. New Modules to Create

These modules introduce the core components of the v5.0 ecosystem. They should be built *before* modifying the existing agent swarm to ensure backward compatibility during the transition.

### `services-python/sycophant/tools/ast_surgeon.py`
* **Purpose:** The ultimate safeguard against LLM hallucinations. It parses Python code, forces it to match a predefined Abstract Syntax Tree (AST) contract (function names, return types), and writes it to disk.
* **Dependencies:** `ast`, `os`.
* **Action:** Create this file first. It is the "Physics Engine" of v5.0.

### `services-python/sycophant/agents/researcher.py`
* **Purpose:** Interfaces with the Gemini 1.5 Flash API to perform sprawling internet research (via Google Search Grounding). It extracts technical briefs and code snippets, bypassing the local context window limit.
* **Dependencies:** `google.generativeai` (or standard `httpx`), `valkyrie_crypto`.
* **Action:** Create this to offload heavy reasoning.

### `services-python/sycophant/orchestrator/fsm.py` (New Folder)
* **Purpose:** A Finite State Machine (FSM) to replace the linear Celery task sequence in `tasks.py`. It manages the dependency graph (e.g., "Don't build `main.py` until `utils.py` passes the sandbox").
* **Dependencies:** `networkx` (optional, for graph math) or standard Python dicts.

---

## 3. Existing Modules to Refactor

These modules require significant updates to support the new Graph-Native architecture.

### `services-python/sycophant/tasks.py`
* **Current State:** A linear, hardcoded sequence (Architect -> Coder -> Tester -> Analyzer -> Deployer).
* **Target State:** Needs to be gutted. It will be replaced by the `fsm.py` logic, which dynamically loops through the AST nodes defined by the Architect.

### `services-python/sycophant/agents/architect.py`
* **Current State:** Uses local Llama 3.1 to generate a flat JSON list of files.
* **Target State:** Needs to use Gemini 1.5 Flash to generate a **Directed Acyclic Graph (DAG)** of dependencies. It must define "Hollow Contracts" (interfaces) instead of just file purposes.

### `services-python/sycophant/agents/coder.py` & `tester.py`
* **Current State:** Reads entire files and relies on Markdown extraction regex. Prone to stuttering and hallucinations.
* **Target State:** Needs to become "Atomic." The prompt should change from "Write this file" to "Fill in the logic for `def func_X()`". It will no longer save directly to disk; it will hand its output to `ast_surgeon.py`.

### `services-python/mnemosyne/app.py` & `ingest.py`
* **Current State:** Simple semantic search over raw text chunks.
* **Target State:** Needs "Tiering." Implement TTL (Time-To-Live) for ephemeral research data, and permanent cold storage for code that passes the Oubliette Sandbox.

### `services-python/oubliette/app.py`
* **Current State:** Runs standard Docker containers.
* **Target State:** Needs to support "Micro-Ephemeral" sandboxing. Boot a fresh container *per node* tested, preventing cross-contamination of state.

---

## 4. Frontend & UI Overhaul (`mission-control`)

The frontend must transition from a "File Explorer" view to a "Spatial Command Center."

### `App.jsx`
* **Current State:** Tabs for logs, flat file trees, and a basic ReactFlow graph.
* **Target State:** * The **ReactFlow Canvas** becomes the primary interface.
    * Implement color-coded node states: Gray (Hollow), Blue (Coding), Green (Verified), Red (Quarantined).
    * Add a "Diff Viewer" pane when clicking a Red node for instant Human-In-The-Loop (HITL) approval.

### `App.css` / `index.css`
* **Current State:** Basic Cyberpunk styling.
* **Target State:** Enhance styling for the new node-based interactions (animations for data flow, pulsing states for active GPU tasks).

---

## 5. Order of Operations (The Upgrade Path)

To avoid breaking the current working v3.0 state, execute the upgrade in this strict sequence:

1. **Build `ast_surgeon.py` (Isolation):** Write the parsing logic and test it completely independently of the swarm. Prove it can fix a broken Python string based on a contract.
2. **Build `researcher.py` (Cloud Link):** Wire up the Gemini API using the existing `valkyrie_crypto` key vault. Verify it can return a condensed technical brief.
3. **Upgrade `architect.py` (The Graph):** Switch the Architect to use Gemini. Modify its prompt to output a JSON Graph instead of a flat list.
4. **Implement `fsm.py` (The Orchestrator):** Replace the linear Celery flow in `tasks.py` with the graph-traversal loop.
5. **Wire the Surgeon to the Coder:** Route the Coder's output through `ast_surgeon.py` before it hits the disk.
6. **Frontend Overhaul:** Once the backend is outputting graph status updates via Redis, update `App.jsx` to visualize the live node states.
