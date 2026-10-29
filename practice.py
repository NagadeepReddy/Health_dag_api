python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py"
)

assert p.is_file(), f"STOP: Missing {p}"

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
    and n.name == "MaxCTAInference"
]

assert len(classes) == 1, "STOP: Unexpected inference class"

cls = classes[0]

print("=== ACTUAL MAX INFERENCE IMPLEMENTATION ===")
print("FILE:", p)

for i in range(cls.lineno, cls.end_lineno + 1):
    print(f"{i}: {lines[i-1]}")

print("\n=== MAX BRIDGE IMPORTS ===")
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        print(ast.get_source_segment(source, node))

print("\n=== BATCHING FEASIBILITY CHECK ===")
print("SINGLE OUTPUT ASSERTION:",
      "(1, 2048)" in source)
print("EXPLICIT BATCH API:",
      any(
          isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
          and "batch" in n.name.lower()
          for n in ast.walk(tree)
      ))

print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
