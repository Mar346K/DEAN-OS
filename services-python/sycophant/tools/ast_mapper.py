import ast
import os

class ProjectMapper:
    """
    Scans a directory and builds a text-based Abstract Syntax Tree (AST) map
    of all Python files, classes, functions, and their arguments.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

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
                    # Get the relative path (e.g., "models/player.py")
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

        output = [f"--- File: {rel_path} ---"]

        for node in tree.body:
            # Extract Classes and their internal methods
            if isinstance(node, ast.ClassDef):
                output.append(f"class {node.name}:")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args]
                        arg_str = ", ".join(args)
                        output.append(f"    def {item.name}({arg_str})")

            # Extract root-level Functions
            elif isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                arg_str = ", ".join(args)
                output.append(f"def {node.name}({arg_str})")

        if len(output) == 1:
            output.append("(No classes or functions defined yet)")

        return "\n".join(output)

if __name__ == "__main__":
    # Quick local test to make sure it works
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))
    mapper = ProjectMapper(test_dir)
    print("--- AST MAP EXPORT ---")
    print(mapper.generate_map())
