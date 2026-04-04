import ast
import astor  # We use astor to easily convert the modified AST back into source code

class ASTSurgeon:
    """
    The deterministic enforcer of DEAN-OS v5.0.
    Ensures LLM-generated code mathematically matches the required structural contracts.
    """
    def __init__(self):
        pass

    def enforce_contract(self, raw_llm_code: str, target_file_contract: dict) -> str:
        """
        Takes raw Python code from the LLM and forcefully applies the required signatures.
        """
        print(f"[AST SURGEON] 🩺 Scrubbing code for: {target_file_contract.get('filename', 'Unknown')}")

        try:
            # 1. Parse the LLM's raw text into a mathematical Abstract Syntax Tree
            tree = ast.parse(raw_llm_code)
        except SyntaxError as e:
            # If the LLM wrote total garbage that isn't even Python, we fail immediately.
            raise ValueError(f"CRITICAL SYNTAX ERROR in LLM output: {e}")

        required_signatures = target_file_contract.get("signatures", [])
        if not required_signatures:
            # If the Architect didn't specify signatures, we just return the code as-is.
            return raw_llm_code

        # 2. Parse the required signatures into their own AST nodes so we can inspect them
        contract_nodes = self._parse_signatures_to_nodes(required_signatures)

        # 3. Perform the Surgery
        # We will iterate through the LLM's code and try to map its functions to our required functions.
        modified_tree = self._perform_surgery(tree, contract_nodes)

        # 4. Stitch the patient back together (AST -> String)
        try:
            clean_code = astor.to_source(modified_tree)
            print("[AST SURGEON] ✅ Surgery successful. Contract enforced.")
            return clean_code
        except Exception as e:
             raise ValueError(f"Failed to unparse AST after surgery: {e}")


    def _parse_signatures_to_nodes(self, signatures: list[str]) -> list:
        """Converts the string signatures from the JSON blueprint into AST nodes."""
        nodes = []
        for sig in signatures:
            # We add a 'pass' body so ast.parse doesn't throw a SyntaxError on just a signature
            clean_sig = sig.strip()
            if not clean_sig.endswith(":"):
                clean_sig += ":"
            dummy_code = f"{clean_sig}\n    pass"

            try:
                parsed = ast.parse(dummy_code)
                # Extract the actual FunctionDef or ClassDef node
                nodes.append(parsed.body[0])
            except Exception as e:
                print(f"[AST SURGEON ⚠️] Warning: Could not parse required signature: '{sig}'. Skipping.")
        return nodes

    def _perform_surgery(self, llm_tree: ast.Module, contract_nodes: list) -> ast.Module:
        """
        Matches LLM functions to Contract functions and forces the LLM functions
        to adopt the Contract's names and arguments, safely updating the internal logic.
        """
        import ast

        llm_functions = [node for node in llm_tree.body if isinstance(node, ast.FunctionDef)]
        contract_functions = [node for node in contract_nodes if isinstance(node, ast.FunctionDef)]

        if len(llm_functions) == 1 and len(contract_functions) == 1:
            target_llm_func = llm_functions[0]
            required_func = contract_functions[0]

            print(f"[AST SURGEON] 🔪 Force-renaming '{target_llm_func.name}' -> '{required_func.name}'")
            target_llm_func.name = required_func.name

            # --- THE DEEP VARIABLE SWAP ---
            # 1. Map the LLM's argument names to the Contract's argument names based on position
            llm_args = [arg.arg for arg in target_llm_func.args.args]
            req_args = [arg.arg for arg in required_func.args.args]

            # Only perform the swap if they have the same number of arguments.
            # If the LLM completely hallucinated the wrong number of inputs, we let the Sandbox catch it.
            if len(llm_args) == len(req_args):
                mapping = dict(zip(llm_args, req_args))

                # 2. Walk through every single node inside the function body
                for node in ast.walk(target_llm_func):
                    # If the node is a Name (variable) and we are loading it (reading it)
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        # If the variable name was one of the original arguments, overwrite it
                        if node.id in mapping:
                            # print(f"Swapping {node.id} for {mapping[node.id]}")
                            node.id = mapping[node.id]

            # 3. Finally, forcefully overwrite the definition signature
            target_llm_func.args = required_func.args
            target_llm_func.returns = required_func.returns

        elif len(contract_functions) > 1:
            print("[AST SURGEON] ⚠️ Multiple signatures required. Advanced mapping not yet implemented. Bypassing surgery.")

        return llm_tree
