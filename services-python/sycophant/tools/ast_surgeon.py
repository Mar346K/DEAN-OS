import ast
import astor  # We use astor to easily convert the modified AST back into source code

class AstComplianceError(Exception):
    """Raised when the Coder violates Zero-Trust physics."""
    pass

class ZeroTrustScanner(ast.NodeVisitor):
    """Walks the AST to detect hardcoded secrets and prohibited operations."""
    def __init__(self):
        self.violations = []
        self.prohibited_imports = {'subprocess', 'pty', 'shlex'}

    def visit_Assign(self, node):
        # 1. Detect Hardcoded Secrets
        if hasattr(node, 'value') and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            val = node.value.value

            # Catch raw API keys
            if val.startswith("sk-") or val.startswith("AIza"):
                self.violations.append(f"Line {node.lineno}: Raw API key detected in string literal. You MUST use valkyrie_crypto.unseal_key().")

            # Catch generic secret variables being assigned raw strings
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(sus in var_name for sus in ['password', 'secret', 'api_key', 'token', 'key']):
                        if len(val) > 3:  # Ignore empty or tiny default strings
                            self.violations.append(f"Line {node.lineno}: Hardcoded secret assigned to variable '{target.id}'. Retrieve this via environment variables or valkyrie_crypto.")

        self.generic_visit(node)

    def visit_Call(self, node):
        # 2. Detect Prohibited Execution Calls (e.g., os.system)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and node.func.attr == 'system':
                self.violations.append(f"Line {node.lineno}: 'os.system' calls are strictly prohibited by Zero-Trust policy.")
        elif isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec']:
                self.violations.append(f"Line {node.lineno}: Dangerous built-in '{node.func.id}' is prohibited.")

        self.generic_visit(node)

    def visit_Import(self, node):
        # 3. Detect Prohibited Imports
        for alias in node.names:
            if alias.name in self.prohibited_imports:
                self.violations.append(f"Line {node.lineno}: Prohibited import '{alias.name}'. Swarm modules may not spawn shell processes.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in self.prohibited_imports:
            self.violations.append(f"Line {node.lineno}: Prohibited from-import '{node.module}'.")
        self.generic_visit(node)


class ASTSurgeon:
    """
    The deterministic enforcer of DEAN-OS v6.0.
    Ensures LLM-generated code mathematically matches the required structural contracts
    AND enforces Zero-Trust compliance before execution.
    """
    def __init__(self):
        pass

    def enforce_contract(self, raw_llm_code: str, target_file_contract: dict) -> str:
        """
        Parses the code, runs the Security Hammer, and forcefully applies required signatures.
        """
        print(f"[AST SURGEON] 🩺 Scrubbing code for: {target_file_contract.get('filename', 'Unknown')}")

        try:
            # 1. Parse the LLM's raw text into a mathematical Abstract Syntax Tree
            tree = ast.parse(raw_llm_code)
        except SyntaxError as e:
            # If the LLM wrote total garbage that isn't even Python, we fail immediately.
            raise AstComplianceError(f"CRITICAL SYNTAX ERROR in LLM output: {e}")

        # --- PHASE 12: THE SECURITY HAMMER ---
        scanner = ZeroTrustScanner()
        scanner.visit(tree)

        if scanner.violations:
            error_report = "\n".join(scanner.violations)
            raise AstComplianceError(f"ZERO-TRUST VIOLATION:\n{error_report}\nFix these issues immediately.")

        # --- EXISTING STRUCTURAL ENFORCEMENT ---
        required_signatures = target_file_contract.get("signatures", [])
        if not required_signatures:
            return raw_llm_code

        # 2. Parse the required signatures into their own AST nodes so we can inspect them
        contract_nodes = self._parse_signatures_to_nodes(required_signatures)

        # 3. Perform the Surgery
        modified_tree = self._perform_surgery(tree, contract_nodes)

        # 4. Stitch the patient back together (AST -> String)
        try:
            clean_code = astor.to_source(modified_tree)
            print("[AST SURGEON] ✅ Surgery successful. Contract enforced.")
            return clean_code
        except Exception as e:
             raise AstComplianceError(f"Failed to unparse AST after surgery: {e}")

    def _parse_signatures_to_nodes(self, signatures: list[str]) -> list:
        """Converts the string signatures from the JSON blueprint into AST nodes."""
        nodes = []
        for sig in signatures:
            clean_sig = sig.strip()
            if not clean_sig.endswith(":"):
                clean_sig += ":"
            dummy_code = f"{clean_sig}\n    pass"

            try:
                parsed = ast.parse(dummy_code)
                nodes.append(parsed.body[0])
            except Exception as e:
                print(f"[AST SURGEON ⚠️] Warning: Could not parse required signature: '{sig}'. Skipping.")
        return nodes

    def _perform_surgery(self, llm_tree: ast.Module, contract_nodes: list) -> ast.Module:
        """
        Matches LLM functions to Contract functions and forces the LLM functions
        to adopt the Contract's names and arguments, safely updating the internal logic.
        """
        llm_functions = [node for node in llm_tree.body if isinstance(node, ast.FunctionDef)]
        contract_functions = [node for node in contract_nodes if isinstance(node, ast.FunctionDef)]

        if len(llm_functions) == 1 and len(contract_functions) == 1:
            target_llm_func = llm_functions[0]
            required_func = contract_functions[0]

            print(f"[AST SURGEON] 🔪 Force-renaming '{target_llm_func.name}' -> '{required_func.name}'")
            target_llm_func.name = required_func.name

            # --- THE DEEP VARIABLE SWAP ---
            llm_args = [arg.arg for arg in target_llm_func.args.args]
            req_args = [arg.arg for arg in required_func.args.args]

            if len(llm_args) == len(req_args):
                mapping = dict(zip(llm_args, req_args))

                for node in ast.walk(target_llm_func):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        if node.id in mapping:
                            node.id = mapping[node.id]

            target_llm_func.args = required_func.args
            target_llm_func.returns = required_func.returns

        elif len(contract_functions) > 1:
            print("[AST SURGEON] ⚠️ Multiple signatures required. Advanced mapping not yet implemented. Bypassing surgery.")

        return llm_tree
