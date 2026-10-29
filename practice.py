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

assert p.is_file(), "STOP: Auxiliary development file missing"

source = p.read_text()
tree = ast.parse(source)
matches = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Call):
        continue
    if not isinstance(n.func, ast.Attribute) or n.func.attr != "reshape":
        continue
    if len(n.args) < 2:
        continue
    if not isinstance(n.args[0], ast.Name):
        continue
    if n.args[0].id not in ("jet0", "jet1"):
        continue

    shape = ast.unparse(n.args[1])
    assert shape in ("[1, 1, 128]", "[2, 1, 128]"), \
        f"STOP: Unexpected JET shape: {shape}"

    matches.append((n.args[0].id, n.args[1], shape))

assert len(matches) == 2
assert {x[0] for x in matches} == {"jet0", "jet1"}

changes = []
lines = source.splitlines(keepends=True)

for name, node, shape in matches:
    if shape == "[1, 1, 128]":
        start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
        end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
        changes.append((start, end))

updated = source

for start, end in sorted(changes, reverse=True):
    updated = updated[:start] + "[2, 1, 128]" + updated[end:]

ast.parse(updated)

if changes:
    backup = p.with_name(p.name + ".before_jetfix.bak")
    assert not backup.exists(), "STOP: Backup already exists"
    backup.write_bytes(p.read_bytes())
    p.write_text(updated)

print("JET0 AND JET1: BATCH-2 SHAPES VERIFIED")
print("RESHAPES: [2,1,128] BOTH")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY

test -f "$DEV/$GRAPH.py"

AUX=$(find "$REPO/artifacts/v1.168-max" \
  /application1/cta_max_true_batch_dev_20261028 \
  -type f -name 'task_embedding.0.weight.npy' \
  -print -quit 2>/dev/null)

test -n "$AUX" || {
  echo "STOP: Previously located auxiliary weights missing"
  exit 1
}

AUX_DIR=$(dirname "$AUX")

echo "=== TRUE BATCH-2 GRAPH CONSTRUCTION ==="

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
import sys
import traceback

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
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
