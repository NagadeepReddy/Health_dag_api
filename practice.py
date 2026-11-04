cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.472/core-artifact/pipeline.py")
source = p.read_text()
tree = ast.parse(source)

print("=== PZAAS EXACT BASE MODEL FACTORY ===")

found = False

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "loadBaseModel":
            found = True
            print("FILE:", p)
            print("LINES:", node.lineno, node.end_lineno)
            print(ast.get_source_segment(source, node))

if not found:
    print("LOAD BASE MODEL FACTORY: NOT FOUND")

print("\n=== BASE MODEL IMPORTS ===")

for node in ast.walk(tree):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        statement = ast.unparse(node)
        if "model" in statement.lower():
            print(statement[:250])

print("\n=== ACTUAL BASE MODEL INITIALIZATION ===")

lines = source.splitlines()

for i, line in enumerate(lines):
    if "self.model_base =" in line:
        for j in range(max(0, i-2), min(len(lines), i+5)):
            print(f"{j+1}: {lines[j]}")

print("\n=== PZAAS MAX GRAPH IDENTITY ===")

g = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)

if g.exists():
    for i, line in enumerate(g.read_text().splitlines()[:32], 1):
        if any(s in line for s in (
            "Graph(", "def build_", "TensorType(",
            "graph.inputs", "remaining"
        )):
            print(f"{i}: {line[:220]}")

print("\nINSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
