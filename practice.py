
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import shutil
import sys

p = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev/pzaas_max_model_adapter.py"
)

print("=== PZAAS VERIFIED GRAPH WEIGHT REPAIR ===", flush=True)

if not p.is_file():
    raise SystemExit(f"STOP: Bridge missing: {p}")

source = p.read_text()
tree = ast.parse(source, filename=str(p))

matches = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.For)
    and isinstance(n.iter, ast.Attribute)
    and isinstance(n.iter.value, ast.Name)
    and n.iter.value.id == "graph"
    and n.iter.attr == "weights"
]

if not matches:
    if "graph_weight_map = graph._weights" in source:
        print("GRAPH WEIGHT ACCESS: ALREADY CORRECTED")
        print("PYTHON SYNTAX: PASS")
        sys.exit(0)
    raise SystemExit(
        "STOP: Expected graph.weights loop not present. "
        "No files modified."
    )

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Found {len(matches)} matching loops. "
        "No files modified."
    )

loop = matches[0]
first = loop.body[0]

if not (
    isinstance(first, ast.Assign)
    and len(first.targets) == 1
    and isinstance(first.targets[0], ast.Name)
    and first.targets[0].id == "name"
):
    raise SystemExit(
        "STOP: Unexpected loop structure. No files modified."
    )

lines = source.splitlines(keepends=True)
original_line = lines[loop.lineno - 1]
indent = original_line[:len(original_line) - len(original_line.lstrip())]

replacement = [
    f"{indent}graph_weight_map = graph._weights\n",
    f"{indent}if not isinstance(graph_weight_map, dict):\n",
    f'{indent}    raise TypeError("MAX graph weight mapping invalid")\n',
    f"{indent}for graph_weight_name, _graph_weight in graph_weight_map.items():\n",
    f"{indent}    name = str(graph_weight_name)\n",
]

lines[loop.lineno - 1:first.end_lineno] = replacement
updated = "".join(lines)

ast.parse(updated, filename=str(p))
compile(updated, str(p), "exec")

backup = p.with_name(p.name + ".pre_registry_fix.bak")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)

assert "for weight in graph.weights:" not in p.read_text()
assert "graph_weight_map = graph._weights" in p.read_text()
ast.parse(p.read_text())

print("GRAPH WEIGHT MAPPING: CORRECTED")
print("REGISTERED WEIGHT KEYS: GRAPH._WEIGHTS")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL BRIDGE BACKUP: SAVED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: VERIFY REAL MAX NATIVE RUNTIME")
PY
