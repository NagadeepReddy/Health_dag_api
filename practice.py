
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)

adapter = root / "pzaas_max_model_adapter.py"
helper = root / "pzaas_live_pack_72.py"

def show(lines, start, end):
    for index in range(max(1, start), min(len(lines), end) + 1):
        print(f"{index:4}: {lines[index - 1]}")

print("=== NATIVE MAX ADAPTER (EXACT HTTP ERROR PATH) ===")
if not adapter.is_file():
    raise SystemExit(f"MISSING: {adapter}")

lines = adapter.read_text().splitlines()
show(lines, 1, 145)

print("\n=== PREVIOUSLY VALIDATED 72-INPUT PACKER ===")
if not helper.is_file():
    raise SystemExit(f"MISSING: {helper}")

source = helper.read_text()
lines = source.splitlines()

print("--- Helper imports and setup ---")
show(lines, 1, 35)

tree = ast.parse(source)
functions = [
    node for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "pack"
]

if not functions:
    print("PACK FUNCTION NOT FOUND")
    show(lines, 36, min(len(lines), 160))
else:
    for node in functions:
        print(f"--- pack() lines {node.lineno}-{node.end_lineno} ---")
        show(lines, node.lineno, node.end_lineno)

print("\n=== INSPECTION COMPLETE: NO FILES MODIFIED ===")
PY
