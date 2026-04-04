# DEAN-OS v5.1: The Sovereign Software Factory

## Architectural Overview
DEAN-OS v5.1 transitions the system from a localized AI code generator into a deterministic, multi-model Surface Mount Technology (SMT) assembly line. It abandons "Global Truth" monolithic prompting in favor of Cellular Isolation, Semantic Hydration, and Compliance-as-Physics.

## The Hierarchy of State (Federated Architecture)
* **Tier 1: The Root (The Universe):** Permanent storage. Contains the Global Master DAG, Compliance Laws, and Cross-Domain API Contracts.
* **Tier 2: The Domain (The Neighborhood):** Project-long storage. Contains shared utilities and context for a specific cluster (e.g., Networking vs. UI).
* **Tier 3: The Scratchpad (The Room):** Ephemeral storage. Contains raw LLM drafts, compiler errors, and local "Neural Zip" hydration.

## The Model-to-Module Matrix (Zero-Budget Optimization)
To maximize capability while minimizing cost, DEAN-OS dynamically routes tasks to specialized, free-tier state-of-the-art models via the `InferenceGateway`.

1.  **The Librarian (Ingestion & Memory):** `NVIDIA Nemotron 3 Super` (Free)
    * **Role:** Semantic Indexer & Context Manager.
    * **Application:** Phase 1 (Neural Zip). Generates the Functional Pointer Graph (FPG) from massive codebases.
2.  **The Workhorse (Brain & Logic):** `Qwen 3.6 Plus` (Free)
    * **Role:** Lead Architect & Agentic Coder.
    * **Application:** Phase 2 (AST Surgeon) and Phase 4 (UI Overhaul). Executes high-complexity agentic coding.
3.  **The Digital Twin (Simulation):** `Gemini 3.1 Flash Lite Preview` ($0.25/M)
    * **Role:** Shadow Scenario Runner.
    * **Application:** Phase 3 (Digital Twin). Rapidly predicts output and maps logical flow before local generation begins.
4.  **The Compliance Officer (Safety):** `Qwen 3.6 Plus` / `GPT-5.4 Nano`
    * **Role:** Policy Enforcement.
    * **Application:** Compliance-as-Physics. Scans for security breaches.

## The "Assembly Line" Flow (FSM 2.0)
1.  **Ingest/Zip:** Legacy code is zipped into Tier 2 Semantic summaries via Nemotron.
2.  **Architect/Twin:** Gemini generates the DAG; the Digital Twin simulates the "Ghost Flow."
3.  **Solder (The Stencil):** `ast_surgeon.py` generates hollow Python files with strict type-hinted signatures.
4.  **Pick & Place (The Muscle):** Qwen-14b/3.6+ fills in the isolated logic blocks.
5.  **X-Ray (Compliance):** The Surgeon enforces Compliance-as-Physics laws (hard-deleting security violations).
6.  **Reflow Oven:** Code is verified in the Oubliette sandbox.
7.  **Librarian:** Successful logic is summarized as a "Lesson Learned" and moved to Tier 1 Memory.

## OpenClaw Interoperability
DEAN-OS is model-agnostic and designed to adhere to the OpenClaw Interop Protocol, allowing seamless integration of future enterprise models (MiMo-V2-Pro, DeepSeek) without pipeline refactoring.

Step 3: Where the New Logic Belongs (Integration Strategy)
To implement this without breaking the clean v5.0 architecture you just built, we need to be surgical about where we place the new code.

Here is the integration map for the Starbucks Sprint:

1. The Multi-Model Router (The Brain Switchboard)

Target File: services-python/sycophant/routing/gateway.py

The Plan: We need to upgrade your InferenceGateway. Instead of just swapping between local qwen-14b and Gemini, we will add dedicated functions like generate_with_nemotron(prompt) and generate_with_qwen36(prompt). We will add a task_type parameter to the main generate function to act as the traffic cop.

2. The Neural Zip (Pillar A)

Target File: Create a new agent: services-python/sycophant/agents/librarian.py

The Plan: This agent will receive large file dumps, route them through the Gateway to Nemotron 3 Super, ask for the Functional Pointer Graph (FPG) JSON, and save that JSON to your Qdrant vector database (MNEMOSYNE).

3. Compliance-as-Physics (Pillar B)

Target File: services-python/sycophant/tools/ast_surgeon.py

The Plan: You asked if we should make the "Security Hammer" adjustable. Absolutely. Hardcoding one level of security is brittle. We will add a security_level="dev" or "prod" parameter to the Surgeon. In "prod" mode, it will actively parse the AST tree looking for ast.Assign nodes where the variable name contains "key" or "secret" and the value is a raw string, and it will physically delete that node.

4. The Digital Twin (Pillar C)

Target File: services-python/sycophant/agents/architect.py

The Plan: We will upgrade the Architect so that after it generates the JSON DAG, it passes the DAG to Gemini 3.1 Flash Lite to perform a "Logical Flow Simulation" to check for circular dependencies before returning the blueprint to the Orchestrator.
