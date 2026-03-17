1. Document Structure: AGENT_SOP.md
This document should be treated as a Tier 1 [TRUTH_SOURCE]. Every agent thread we build will reference these specific rules during initialization.

Section 1: The Reasoning Loop (Chain of Thought)
Rule: No agent is permitted to output raw code as a first response.

Protocol: Every task must follow the Plan-Execute-Review cycle.

Plan: The agent outputs a structured logic map.

Execute: The agent writes the code based on that map.

Review: The agent "simulates" an error-check before finalizing.

Section 2: Context Injection (The 8B Model Strategy)
Rule: Minimize "Guesswork."

Protocol: Before an agent answers, the Mnemosyne-Vault must inject the top 3 most relevant documentation snippets from truth_db. The prompt must explicitly state: "Use ONLY the provided documentation below to solve the task."

Section 3: Micro-Tasking (The Atomic Unit Rule)
Rule: Never request more than one "Module" or "Function" at a time.

Protocol: Large features (e.g., "Build a JWT Validator") must be broken into atomic sub-tasks by the Librarian before being sent to the Hephaestus-Daemon.

2. Programmatic Enforcement (The "How")
To make sure this isn't just a document you "hope" the AI follows, we build it into the DAEN-OS Switchboard and agent classes.

A. The Librarian’s "Thinking" Constraint
In Thread 4 (The Agents), we will code the Librarian so it uses a Two-Stage Request.

Stage 1: The Switchboard asks the Librarian for a Plan.

Stage 2: Once the Plan is received, the Switchboard sends that Plan back to the Librarian and says, "Now, write the Python code based strictly on your verified plan." * Benefit: This offsets the 8B model's tendency to rush, forcing it to use its own planning as a "Context Anchor."

B. The Oubliette-Lab (Sandbox) Feedback Loop
Instead of you manually pasting errors, the Oubliette-Lab is programmed to "Self-Correct."

Logic: 1. The Sandbox detects a SyntaxError or AssertionError.
2. It automatically bundles the Error Log + The Code + The Original Task.
3. It sends it back to the agent with the prompt: "I encountered this error in the Sandbox. Identify the cause, correct it, and output the updated code."

Result: The system performs 2–3 "Internal Retries" before ever showing you the result.

C. Template-Based Prompting
We will create a PROMPT_TEMPLATES folder in the monorepo. Every time a Sycophant-Agent starts, it pulls a template that includes the "Rules of Engagement" you listed (e.g., "Prefer early returns," "No classes unless necessary"). This keeps the 8B model's style consistent with your personal coding preferences.

3. Why this fits the "Source of Truth"
By having an AGENT_SOP.md, you are showing a hiring manager that you understand Model Governance. You aren't just using AI; you are managing a fleet of agents with strict quality-control standards.