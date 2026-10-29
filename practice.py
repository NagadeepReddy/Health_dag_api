cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029

python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

src = root / "artifacts/v1.168-max/cta_max/grecbase_aux_branches_max.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_mainfix.py"

dst = dev / "grecbase_aux_branches_max_batch2_fix.py"
newgraph = dev / "grecbase_fusion_full_head_72_max_batch2_auxfix.py"

assert src.is_file() and graph.is_file(), "STOP: Verified source missing"

code = src.read_text()
tree = ast.parse(code)
fixes = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "task" for t in n.targets):
        continue

    call = n.value
    if not isinstance(call, ast.Call) or len(call.args) < 2:
        continue
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "reshape":
        continue
    if ast.unparse(call.args[1]) == "[1, 256]":
        fixes.append(call.args[1])

assert len(fixes) == 1, f"STOP: Task reshape matches: {len(fixes)}"
fixes[0].elts[0] = ast.Constant(value=2)

for n in ast.walk(tree):
    if isinstance(n, ast.ImportFrom) and n.level:
        assert n.level == 1 and n.module
        n.module = "cta_max." + n.module
        n.level = 0

ast.fix_missing_locations(tree)
updated = ast.unparse(tree) + "\n"
compile(updated, str(dst), "exec")

gtree = ast.parse(graph.read_text())
imports = [
    n for n in ast.walk(gtree)
    if isinstance(n, ast.ImportFrom)
    and n.module == "cta_max.grecbase_aux_branches_max"
]

assert len(imports) == 1, \
    f"STOP: Auxiliary import count: {len(imports)}"

imports[0].module = "grecbase_aux_branches_max_batch2_fix"
ast.fix_missing_locations(gtree)

gcode = ast.unparse(gtree) + "\n"
compile(gcode, str(newgraph), "exec")

for path, content in ((dst, updated), (newgraph, gcode)):
    if path.exists():
        assert path.read_text() == content, \
            f"STOP: Existing file differs: {path}"
        print("VERIFIED:", path.name)
    else:
        path.write_text(content)
        print("CREATED:", path.name)

print("TASK BATCH SHAPE FIX: [1,256] -> [2,256]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS AND WORKING RELEASE: UNCHANGED")
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
  -v "$REPO:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$REPO/artifacts/v1.168-max/cta_max/main_context_weights:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import traceback

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_auxfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    print("TRUE BATCH-2 GRAPH BUILD: START", flush=True)

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

print("TRUE BATCH-2 INFERENCE: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
