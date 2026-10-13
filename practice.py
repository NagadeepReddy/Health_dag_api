cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import ast
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
g = b / "grecbase_fusion_full_head_72_max.py"
r = b / "run_real_sanity_full_head_72.py"

tree = ast.parse(g.read_text())
runner = ast.parse(r.read_text())

print("=== INTEGRATED GRAPH ===")
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        fn = ast.unparse(node.func)
        if fn in ("graph.output",
                  "grecbase_get_path_max",
                  "grecbase_get_path_reference_max"):
            print(node.lineno, ast.unparse(node))

print("=== RUNNER IMPORT ===")
for node in ast.walk(runner):
    if isinstance(node, ast.ImportFrom):
        if "grecbase" in (node.module or ""):
            print(node.lineno, ast.unparse(node))

print("=== RUNNER OUTPUT SELECTION ===")
for i, line in enumerate(r.read_text().splitlines(), 1):
    if "model.execute(" in line or "outputs[0]" in line or "enumerate(outputs)" in line:
        print(i, line.strip())
PY
