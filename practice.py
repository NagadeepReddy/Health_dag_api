python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")

targets = {
    "build_grecbase_fusion_graph_order_correct",
    "build_real_inputs",
}

found = {}

for p in sorted(root.rglob("*.py")):
    if any(x in p.name.lower() for x in (".bak", "backup")):
        continue

    try:
        source = p.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError):
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in targets:
                found.setdefault(node.name, []).append((p, node, source.splitlines()))

print("=== TRUE MAX BATCHING FEASIBILITY ===")

terms = (
    "shape", "batch", "tensor", "input",
    "dimension", "dim=", "symbolic",
    "static", "reshape", "stack", "concat",
    "graph", "model_in", "vl_in",
)

for name in sorted(targets):
    print("\nFUNCTION:", name)
    matches = found.get(name, [])

    if not matches:
        print("NOT FOUND")
        continue

    for p, node, lines in matches:
        print("SOURCE:", p)
        print("LINES:", node.lineno, "-", node.end_lineno)

        shown = set()
        for i in range(node.lineno-1, node.end_lineno):
            if any(t in lines[i].lower() for t in terms):
                for j in range(max(node.lineno-1, i-1),
                               min(node.end_lineno, i+2)):
                    if j not in shown:
                        print(f"{j+1}: {lines[j][:180]}")
                        shown.add(j)
                    if len(shown) >= 100:
                        break
            if len(shown) >= 100:
                print("OUTPUT LIMITED TO 100 LINES")
                break

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
