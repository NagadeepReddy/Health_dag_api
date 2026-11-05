
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_max_model_adapter.py")
assert p.is_file(), f"Missing bridge: {p}"

source = p.read_text()
old = """            for weight in graph.weights:
                name = str(getattr(weight, "name", weight))"""

new = """            raw_weights = getattr(graph, "_weights", None)
            if raw_weights is None:
                raise RuntimeError("MAX graph weight registry unavailable")
            if isinstance(raw_weights, dict):
                entries = raw_weights.items()
            else:
                entries = [
                    (getattr(w, "name", str(i)), w)
                    for i, w in enumerate(raw_weights)
                ]
            for graph_weight_name, weight in entries:
                name = str(getattr(weight, "name", graph_weight_name))"""

assert source.count(old) == 1, "Expected source pattern not found"
updated = source.replace(old, new)
ast.parse(updated)

backup = p.with_suffix(".before_weight_fix.bak")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)
compile(p.read_text(), str(p), "exec")

print("=== PZAAS NATIVE BRIDGE CORRECTION ===")
print("GRAPH WEIGHT ACCESS: CORRECTED")
print("BRIDGE BACKUP: SAVED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: MAX CONTAINER RUNTIME VALIDATION")
PY
