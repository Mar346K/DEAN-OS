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
