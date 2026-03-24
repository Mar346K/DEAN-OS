Phase 21: The Neural Override (HITL Bidirectional Bridge)
The Current State: If the swarm fails 3 times, your UI pops up the neon magenta Human-In-The-Loop modal. However, typing a hint and clicking "SUBMIT_FIX" just prints to console.log. The AI is still frozen.

The Build: We need to create a new endpoint (/hitl/resolve) in manager.py. When you click "Submit", the UI sends your text to this endpoint, which unfreezes the Manager, injects your human hint directly into the Coder's prompt, and resets the attempt counter so the swarm can try again.

Phase 22: The CI/CD Capstone (Wiring the Deployer)
The Current State: When the Analyzer finally passes the code in the Sandbox, the Manager just prints "Assembly Line Complete" and stops. The code stays trapped in the staging/workspace.

The Build: We need to import your Deployer agent into manager.py. Once the code passes QA, the Manager will trigger Deployer().deploy_module(), which will physically migrate the validated code from the messy sandbox into your pristine, production workspace folder.

Phase 23: Live Cartography (Dynamic Blast Radius)
The Current State: The "BLAST_RADIUS" graph on your React UI looks cool, but the nodes are currently hardcoded to show main.py just for UI testing purposes.

The Build: We are going to wire your tools/ast_mapper.py into the WebSocket payload. Whenever the Deployer moves a file, the Manager will run the ProjectMapper, generate the real AST (Abstract Syntax Tree) JSON, and broadcast it to the UI. Your React Flow graph will dynamically draw the actual architecture of your project as the AI builds it.
