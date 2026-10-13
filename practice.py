python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_real_shapes_max.py")
assert p.is_file(), f"Missing: {p}"

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

print("=== COMBINED GRAPH INPUT CONTRACT ===")

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    if not isinstance(node.func, ast.Name) or node.func.id != "Graph":
        continue
    print("GRAPH LINE:", node.lineno)
    for kw in node.keywords:
        if kw.arg == "input_types":
            print("INPUT TYPES:")
            print(ast.unparse(kw.value))

print("\n=== INPUT ORDER AND BRANCH CONNECTIONS ===")

patterns = (
    ".inputs[", "graph.inputs", "input_types=",
    "deep_inputs", "wide_inputs", "seq_inputs",
    "context_inputs", "sibling_inputs"
)

shown = set()
for i, line in enumerate(lines):
    if any(pattern in line for pattern in patterns):
        for j in range(max(0, i-1), min(len(lines), i+2)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
