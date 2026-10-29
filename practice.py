cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
p = dev / "nlp_bert_in_graph_batch2_contextfix.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_bertcontextfix.py"

assert p.is_file() and graph.is_file(), "STOP: Verified files missing"

code = p.read_text()
tree = ast.parse(code)
matches = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "cls" for t in node.targets):
        continue
    call = node.value
    if not isinstance(call, ast.Call) or len(call.args) < 2:
        continue
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "reshape":
        continue
    matches.append(call.args[1])

assert len(matches) == 1, f"STOP: CLS reshape count = {len(matches)}"
shape = matches[0]

if ast.unparse(shape) == "[2, 384]":
    print("CLS BATCH-2 FIX: ALREADY INSTALLED")
else:
    assert ast.unparse(shape) == "[1, 384]", \
        f"STOP: Unexpected CLS shape: {ast.unparse(shape)}"

    lines = code.splitlines(keepends=True)
    start = sum(map(len, lines[:shape.lineno - 1])) + shape.col_offset
    end = sum(map(len, lines[:shape.end_lineno - 1])) + shape.end_col_offset

    updated = code[:start] + "[2, 384]" + code[end:]
    compile(updated, str(p), "exec")

    backup = p.with_name(p.name + ".before_clsfix.bak")
    assert not backup.exists(), "STOP: Existing backup requires review"
    backup.write_bytes(p.read_bytes())
    p.write_text(updated)
    print("CLS BATCH-2 FIX: INSTALLED")

print("CLS SHAPE: [1,384] -> [2,384]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY

echo "=== RETRY TRUE BATCH-2 GRAPH ==="

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

print("REAL BATCH-2 GRAPH BUILD: START", flush=True)

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_bertcontextfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

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
