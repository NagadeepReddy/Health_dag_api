python - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.168-max/cta_max")

print("=== EXISTING FULL-GRAPH ENTRY POINTS ===")
for p in sorted(root.glob("*.py")):
    source = p.read_text()
    if not any(s in source for s in (
        "grecbase_eight_branch_fusion",
        "build_grecbase_fusion",
        "grecbase_get_path_max",
        "REAL CTA MAX EXECUTION"
    )):
        continue
    tree = ast.parse(source)
    print("\nFILE:", p.name)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            print(" ", node.name, "line", node.lineno)
    for i, line in enumerate(source.splitlines(), 1):
        if any(s in line for s in (
            "Graph(", "graph.output(", "session.load(",
            "model.execute(", "grecbase_get_path_max("
        )):
            print(f"  {i}: {line.strip()[:140]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
