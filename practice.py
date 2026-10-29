python3 -S -B - <<'PY'
from pathlib import Path
import ast

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
p = repo / "artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py"

assert p.is_file(), f"STOP: Bridge missing: {p}"

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

print("=== EXISTING MAX INFERENCE BRIDGE ===")
print("SOURCE:", p)

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f"FUNCTION: {node.name} | lines {node.lineno}-{node.end_lineno}")

print("\n=== BATCHING / MAX EXECUTION POINTS ===")

terms = (
    "session.execute",
    "session.run",
    "model.execute",
    "model.run",
    "max_engine",
    "max_session",
    "InferenceSession",
    "load_model",
    "predict_raw",
    "batch_size",
    "batch",
    "reshape",
    "concat",
    "stack",
    "attach_max",
)

matches = [
    i for i, line in enumerate(lines)
    if any(term.lower() in line.lower() for term in terms)
]

shown = set()
for i in matches:
    for j in range(max(0, i-2), min(len(lines), i+4)):
        if j not in shown:
            print(f"{j+1}: {lines[j][:180]}")
            shown.add(j)
    print("---")

print("\nBRIDGE REVIEW: COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
