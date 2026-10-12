python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename, function in (
    ("grecbase_max.py", "__call__"),
    ("grecbase_fusion_graph_max.py", "build_grecbase_fusion_graph"),
):
    p = base / filename
    lines = p.read_text().splitlines()
    tree = ast.parse(p.read_text())

    print(f"\n===== {filename}: {function} =====")

    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function:
            found = True
            end = min(node.end_lineno, node.lineno + 89)
            for n in range(node.lineno, end + 1):
                print(f"{n}: {lines[n-1]}")
            if end < node.end_lineno:
                print(f"... {node.end_lineno-end} additional lines omitted")
            break

    if not found:
        print("FUNCTION NOT FOUND")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
