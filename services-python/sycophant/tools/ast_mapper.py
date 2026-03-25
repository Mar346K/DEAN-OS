import ast
import os
try:
    import git
except ImportError:
    git = None

class ProjectMapper:
    """
    [PHASE 17: FORENSIC HARVESTER]
    Scans a directory to build a text-based PIM and a visual Graph structure.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.churn_data = self._calculate_git_churn()

    def _calculate_git_churn(self) -> dict:
        churn = {}
        if not git:
            return churn
        try:
            repo = git.Repo(self.workspace_path, search_parent_directories=True)
            for commit in repo.iter_commits(max_count=100):
                for file_path in commit.stats.files:
                    normalized = os.path.basename(file_path)
                    churn[normalized] = churn.get(normalized, 0) + 1
        except Exception:
            pass # nosec B110
        return churn

    def generate_map(self) -> str:
        if not os.path.exists(self.workspace_path):
            return "Workspace is currently empty."

        repo_map = []
        IGNORE_DIRS = {'__pycache__', 'venv', 'env', '.venv', '.env', 'node_modules', 'site-packages', 'dist', 'build'}

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORE_DIRS]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.workspace_path).replace("\\", "/")
                    repo_map.append(self._parse_file(file_path, rel_path))

        if not repo_map:
            return "No Python files currently exist in the workspace."
        return "\n\n".join(repo_map)

    def _parse_file(self, file_path: str, rel_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            return f"--- File: {rel_path} ---\n[Error parsing file: {e}]"

        basename = os.path.basename(file_path)
        churn_score = self.churn_data.get(basename, 0)
        risk_level = "HIGH RISK (Scar Tissue)" if churn_score > 5 else "Normal"
        output = [f"--- File: {rel_path} | Churn Score: {churn_score} ({risk_level}) ---"]

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                output.append(f"class {node.name}:")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args]
                        calls = [n.func.id for n in ast.walk(item) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                        call_str = f" -> Calls: {list(set(calls))}" if calls else ""
                        output.append(f"    def {item.name}({', '.join(args)}){call_str}")
            elif isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                calls = [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                call_str = f" -> Calls: {list(set(calls))}" if calls else ""
                output.append(f"def {node.name}({', '.join(args)}){call_str}")

        if len(output) == 1:
            output.append("(No classes or functions defined yet)")
        return "\n".join(output)

    def generate_ui_graph(self) -> dict:
        """Returns JSON nodes and edges for the ReactFlow UI."""
        nodes = []
        edges = []
        IGNORE_DIRS = {'__pycache__', 'venv', 'env', '.venv', '.env', 'node_modules', 'site-packages', 'dist', 'build'}
        file_registry = {}

        # 1. Register all files
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORE_DIRS]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, self.workspace_path).replace("\\", "/")
                    file_registry[rel_path] = abs_path

                    basename = os.path.basename(abs_path)
                    nodes.append({"id": rel_path, "group": "python", "churn_score": self.churn_data.get(basename, 0)})

        # 2. Build a fuzzy lookup dictionary matching python imports to paths
        module_lookup = {}
        for rel in file_registry.keys():
            no_ext = rel.replace(".py", "") # "NexusMapper/src/scanner"
            parts = no_ext.split("/")

            # Register every combination: "scanner", "src.scanner", "NexusMapper.src.scanner"
            for i in range(len(parts)):
                mod_name = ".".join(parts[i:])
                module_lookup[mod_name] = rel

        # 3. Parse ASTs to find imports and draw edges
        for rel_path, abs_path in file_registry.items():
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            target = module_lookup.get(alias.name)
                            if target and target != rel_path:
                                edges.append({"source": rel_path, "target": target})
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        target = module_lookup.get(node.module)
                        if target and target != rel_path:
                            edges.append({"source": rel_path, "target": target})
            except Exception: # nosec B110
                pass

        # Deduplicate edges
        unique_edges = []
        seen = set()
        for edge in edges:
            uid = f"{edge['source']}->{edge['target']}"
            if uid not in seen:
                seen.add(uid)
                unique_edges.append(edge)

        return {"nodes": nodes, "edges": unique_edges}
