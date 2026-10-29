cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
GRAPH=grecbase_fusion_full_head_72_max_batch2_auxfix

python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
p = dev / "grecbase_aux_branches_max_batch2_fix.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_auxfix.py"

assert p.is_file() and graph.is_file(), "STOP: Required files missing"

source = p.read_text()
tree = ast.parse(source)

matches = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Return):
        continue
    call = node.value
    if not isinstance(call, ast.Call) or len(call.args) != 2:
        continue
    if not isinstance(call.func, ast.Attribute):
        continue
    if call.func.attr != "reshape":
        continue
    if not isinstance(call.func.value, ast.Name) or call.func.value.id != "ops":
        continue
    inner = call.args[0]
    if not isinstance(inner, ast.Call) or not isinstance(inner.func, ast.Attribute):
        continue
    if inner.func.attr != "concat":
        continue
    if ast.unparse(call.args[1]) == "[1, 2 * dim]":
        matches.append(call.args[1])

assert len(matches) == 1, f"STOP: Expected one pooling reshape, found {len(matches)}"

shape = matches[0]
lines = source.splitlines(keepends=True)
start = sum(map(len, lines[:shape.lineno - 1])) + shape.col_offset
end = sum(map(len, lines[:shape.end_lineno - 1])) + shape.end_col_offset

updated = source[:start] + "[2, 2 * dim]" + source[end:]
ast.parse(updated)

backup = p.with_name(p.name + ".before_poolfix.bak")
assert not backup.exists(), "STOP: Backup already exists"
backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("AUXILIARY POOLING FIX: INSTALLED")
print("RESHAPE: [1,256] -> [2,256]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
PY

AUX=$(find \
  "$REPO/artifacts/v1.168-max" \
  /application1/cta_max_true_batch_dev_20261028 \
  -type f -name 'task_embedding.0.weight.npy' \
  -print -quit 2>/dev/null)

test -n "$AUX" || { echo "STOP: Auxiliary weights missing"; exit 1; }
AUX_DIR=$(dirname "$AUX")

echo "=== REAL BATCH-2 GRAPH REBUILD ==="

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
  -v "$AUX_DIR:/weights_aux:ro" \
  -v "$REPO/artifacts/v1.168-max/cta_max/main_context_weights:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_auxfix import (
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
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
