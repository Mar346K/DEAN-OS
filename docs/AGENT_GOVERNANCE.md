# AGENT_GOVERNANCE.md: Deterministic Reasoning Protocols


## 1. Vision & Purpose


AI agents are prone to "rushing" and "hallucination" when given complex, multi-step tasks. DEAN-OS solves this by implementing a **Deterministic Governance Layer**.


We treat agentic reasoning as a regulated industrial process, moving from "black-box prompting" to a structured, repeatable **Assembly Line**.


---


## 2. The Reasoning Loop: Plan-Execute-Verify


No agent in the DEAN-OS swarm is permitted to output raw code as a first response. Every task must follow the **PEV Cycle**:


1. **PLAN:** The agent outputs a structured logic map and dependency tree. This serves as a "Context Anchor."


2. **EXECUTE:** The agent writes the code based strictly on the verified plan from step one.


3. **VERIFY:** The agent "simulates" an error-check (Self-Correction) before the payload is ever sent to the Sandbox.


---


## 3. Micro-Tasking: The Atomic Unit Rule


To prevent the "Cognitive Ceiling" of local models from being reached, DEAN-OS enforces **Atomic Tasking**.


* **The Protocol:** Large features (e.g., "Build a JWT Validator") are never sent as a single prompt.


* **The Breakout:** The **Librarian Agent** decomposes the feature into atomic sub-tasks (e.g., "Write the RSA public key loader," then "Write the signature verifier").


* **Sequential Execution:** Agents handle one sub-task at a time. This keeps the "Attention Head" focused on specific logic, drastically reducing the probability of syntax errors.


---


## 4. Context Injection: The [TRUTH_SOURCE] Strategy


"Guessing" is the primary cause of LLM failure. DEAN-OS replaces guesswork with **Hardcoded Context Injection**.


* **Mnemosyne-Vault Integration:** Before an agent begins a task, the RAG engine injects the top three most relevant documentation snippets from the `truth_db`.


* **Strict Grounding:** The prompt explicitly instructs the agent: *"Use ONLY the provided documentation below to solve the task. If the info is not present, report a KNOWLEDGE_GAP."*


* **Impact:** This ensures that even if a library (like `PyO3`) has updated its API, the agent uses the current docs you've provided, not its outdated training data.


---


## 5. Self-Healing & HITL Fail-safes


DEAN-OS implements an autonomous **Self-Correction Loop** with a Human-In-The-Loop (HITL) circuit breaker.


* **Oubliette Feedback:** If a test fails in the Sandbox, the error log, the original code, and the task are bundled and sent back to the agent for "Self-Healing."


* **Recursive Limit:** The system performs exactly two internal retries.


* **The Magenta Modal:** If the second retry fails, the system triggers the **Human-In-The-Loop** protocol. It halts the swarm and presents the code and the error to the user for a one-sentence "Hint," which the agent then uses to finalize the fix.


---


## 6. Template-Based Prompting


To maintain a consistent "Senior" coding style (e.g., preferring early returns, no unnecessary classes, strict type-hinting), DEAN-OS utilizes **Immutable Prompt Templates**.


Every agent initialization pulls from the `PROMPT_TEMPLATES` directory, ensuring the swarm adheres to your specific engineering standards regardless of the underlying model being used.
