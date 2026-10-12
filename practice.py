python - <<'PY'
import ast
from pathlib import Path

files = [
    Path("artifacts/v1.168/utils/dependency-utils/models.py"),
    Path("artifacts/v1.168-max/cta_max/grecbase_get_path_max.py"),
]

for p in files:
    print(f"\n===== {p.name} =====")
    src = p.read_text()
    lines = src.splitlines()
    tree = ast.parse(src)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and (
            node.name == "get_path" or
            node.name == "grecbase_get_path_max"
        ):
            print("ARGUMENTS:", ast.unparse(node.args))
            for n in range(node.lineno, min(node.end_lineno, node.lineno + 44) + 1):
                print(f"{n}: {lines[n-1]}")
            if node.end_lineno > node.lineno + 44:
                print("... remaining lines omitted")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
