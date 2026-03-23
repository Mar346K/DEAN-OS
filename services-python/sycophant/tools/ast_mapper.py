import ast
import os
try:
    import git
except ImportError:
    git = None

class ProjectMapper:
    """
    [PHASE 17: FORENSIC HARVESTER]
    Scans a directory to build a text-based Project Intelligence Manifest (PIM).
    Extracts AST skeletons, Call-Graphs (Blast Radius), and Git Churn (Scar Tissue).
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        # Harvest Git Churn Data on initialization
        self.churn_data = self._calculate_git_churn()

    def _calculate_git_churn(self) -> dict:
        """Analyzes the .git history to find 'Scar Tissue' (highly modified files)."""
        churn = {}
        if not git:
            return churn

        try:
            # search_parent_directories=True allows it to find the root DEAN-OS .git folder
            # even if the workspace is nested deep in staging/workspace
            repo = git.Repo(self.workspace_path, search_parent_directories=True)

            # Analyze the last 100 commits for volatility
            for commit in repo.iter_commits(max_count=100):
                for file_path in commit.stats.files:
                    # Normalize paths to match our AST crawler
                    normalized = os.path.basename(file_path)
                    churn[normalized] = churn.get(normalized, 0) + 1
        except Exception:
            # Fails gracefully if no .git repo is found (e.g., inside a pure Docker container)
            pass # nosec B110

        return churn

    def generate_map(self) -> str:
        if not os.path.exists(self.workspace_path):
            return "Workspace is currently empty."

        repo_map = []
        # Walk the directory tree, ignoring hidden folders and __pycache__
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith(".py"):
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
            # Compile the source code into an Abstract Syntax Tree
            tree = ast.parse(source)
        except SyntaxError:
            return f"--- File: {rel_path} ---\n[Syntax Error - Could not parse structure]"
        except Exception as e:
            return f"--- File: {rel_path} ---\n[Error reading file: {e}]"

        # Lookup Churn Score for this specific file
        basename = os.path.basename(file_path)
        churn_score = self.churn_data.get(basename, 0)
        risk_level = "HIGH RISK (Scar Tissue)" if churn_score > 5 else "Normal"

        output = [f"--- File: {rel_path} | Churn Score: {churn_score} ({risk_level}) ---"]

        for node in tree.body:
            # Extract Classes and their internal methods
            if isinstance(node, ast.ClassDef):
                output.append(f"class {node.name}:")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args]
                        arg_str = ", ".join(args)

                        # [Phase 17] Call-Graph Extraction
                        calls = [n.func.id for n in ast.walk(item) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                        call_str = f" -> Calls: {list(set(calls))}" if calls else ""

                        output.append(f"    def {item.name}({arg_str}){call_str}")

            # Extract root-level Functions
            elif isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                arg_str = ", ".join(args)

                # [Phase 17] Call-Graph Extraction
                calls = [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                call_str = f" -> Calls: {list(set(calls))}" if calls else ""

                output.append(f"def {node.name}({arg_str}){call_str}")

        if len(output) == 1:
            output.append("(No classes or functions defined yet)")

        return "\n".join(output)

if __name__ == "__main__":
    # Point it at its own DEAN-OS root directory to test the Git Churn logic!
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    mapper = ProjectMapper(test_dir)
    print("--- FORENSIC PIM EXPORT ---")
    print(mapper.generate_map())
