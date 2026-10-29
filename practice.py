cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = Path("artifacts/v1.168-max/cta_max/main_context_max.py")
graph = dev / "grecbase_fusion_full_head_72_max_batch2_bertcontextfix.py"

dst = dev / "main_context_max_batch2_fix.py"
newgraph = dev / "grecbase_fusion_full_head_72_max_batch2_mainfix.py"

assert src.is_file() and graph.is_file(), "STOP: Required source missing"

tree = ast.parse(src.read_text())
functions = [
    n for n in tree.body
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == "main_context_forward"
]
assert len(functions) == 1, "STOP: Main context function differs"

matches = []
for n in ast.walk(functions[0]):
    if not isinstance(n, ast.Call) or len(n.args) < 2:
        continue
    if not isinstance(n.func, ast.Attribute) or n.func.attr != "reshape":
        continue
    try:
        shape = ast.literal_eval(n.args[1])
    except (ValueError, TypeError):
        continue
    if shape == [1, 128]:
        matches.append(n.args[1])

assert len(matches) == 1, \
    f"STOP: Expected one [1,128] reshape; found {len(matches)}"

shape = matches[0]
shape.elts[0] = ast.Constant(value=2)

# Preserve imports of original MAX integration dependencies.
for n in ast.walk(tree):
    if isinstance(n, ast.ImportFrom) and n.level == 1:
        assert n.module, "STOP: Unsupported relative import"
        n.module = "cta_max." + n.module
        n.level = 0

ast.fix_missing_locations(tree)
updated = ast.unparse(tree) + "\n"
compile(updated, str(dst), "exec")

gtree = ast.parse(graph.read_text())
imports = [
    n for n in ast.walk(gtree)
    if isinstance(n, ast.ImportFrom)
    and n.module == "cta_max.main_context_max"
    and any(a.name == "main_context_forward" for a in n.names)
]
assert len(imports) == 1, \
    f"STOP: Main context import count = {len(imports)}"

imports[0].module = "main_context_max_batch2_fix"
ast.fix_missing_locations(gtree)
gcode = ast.unparse(gtree) + "\n"
compile(gcode, str(newgraph), "exec")

for p, content in ((dst, updated), (newgraph, gcode)):
    if p.exists():
        assert p.read_text() == content, \
            f"STOP: Existing candidate differs: {p}"
        print("VERIFIED:", p.name)
    else:
        p.write_text(content)
        print("CREATED:", p.name)

print("MAIN CONTEXT BATCH FIX: INSTALLED")
print("SHAPE: [1,128] -> [2,128]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS AND MAX FILES: UNCHANGED")
PY

echo "=== TRUE BATCH-2 GRAPH REBUILD ==="

timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max \
  -v "$PWD:/workspace:ro" \
  -v /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029:/batch2:ro \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_mainfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    print("REAL BATCH-2 GRAPH BUILD: START", flush=True)
    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("INPUT COUNT:", len(graph.inputs))
    for i, item in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", item.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
