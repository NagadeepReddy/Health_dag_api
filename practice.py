cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029

python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "grecbase_fusion_full_head_72_max_batch2_auxfix.py"
dst = dev / "grecbase_fusion_full_head_72_max_batch2_diagnostic.py"

assert src.is_file(), "STOP: Existing batch-2 graph missing"

code = src.read_text()
tree = ast.parse(code)
matches = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "outs"
               for t in n.targets):
        continue
    if not isinstance(n.value, ast.Call):
        continue
    if not isinstance(n.value.func, ast.Attribute):
        continue
    if n.value.func.attr != "concat":
        continue

    matches.append(n)

assert len(matches) == 1, "STOP: Unexpected fusion structure"

node = matches[0]
assert isinstance(node.value.args[0], ast.ListComp)

comp = node.value.args[0]
assert len(comp.generators) == 1

items = comp.generators[0].iter
assert isinstance(items, (ast.Tuple, ast.List))

names = []
for item in items.elts:
    assert isinstance(item, ast.Name), "STOP: Unexpected branch"
    names.append(item.id)

assert len(names) == 8, f"STOP: Expected 8 branches, found {names}"

lines = code.splitlines(keepends=True)
original = lines[node.lineno - 1]
indent = original[:len(original) - len(original.lstrip())]

diagnostic = [
    indent + 'print("=== ALL EIGHT REAL BATCH-2 BRANCH SHAPES ===", flush=True)\n'
]

for name in names:
    diagnostic.append(
        indent +
        f'print("{name}:", {name}.type.shape, flush=True)\n'
    )

diagnostic.append(
    indent + 'print("SHAPE AUDIT COMPLETE — NO RESHAPES APPLIED", flush=True)\n'
)
diagnostic.append(indent + "return None\n")

updated = (
    "".join(lines[:node.lineno - 1])
    + "".join(diagnostic)
    + "".join(lines[node.lineno - 1:])
)

compile(updated, str(dst), "exec")

if dst.exists():
    assert dst.read_text() == updated, "STOP: Existing diagnostic differs"
else:
    dst.write_text(updated)

print("EIGHT-BRANCH DIAGNOSTIC: READY")
print("BRANCHES:", ", ".join(names))
print("ORIGINAL GRAPH: UNCHANGED")
print("DS CODE: UNCHANGED")
PY

AUX=$(find "$REPO/artifacts/v1.168-max" \
  /application1/cta_max_true_batch_dev_20261028 \
  -type f -name 'task_embedding.0.weight.npy' \
  -print -quit 2>/dev/null)

test -n "$AUX" || {
  echo "STOP: Auxiliary weights missing"
  exit 1
}

echo "=== CHECK ALL EIGHT BRANCHES ==="

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
  -v "$(dirname "$AUX"):/weights_aux:ro" \
  -v "$REPO/artifacts/v1.168-max/cta_max/main_context_weights:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
from max.driver import CPU
from max.graph import DeviceRef

from grecbase_fusion_full_head_72_max_batch2_diagnostic import (
    build_grecbase_fusion_graph_order_correct_batch2_shapes
)

result = build_grecbase_fusion_graph_order_correct_batch2_shapes(
    DeviceRef.from_device(CPU())
)

assert result is None, "STOP: Diagnostic unexpectedly returned a graph"

print("COMPLETE EIGHT-BRANCH SHAPE AUDIT: PASS")
print("REAL BATCH-2 EXECUTION: NOT PERFORMED")
print("ORIGINAL DS AND WORKING RELEASE: UNCHANGED")
PY
SH
