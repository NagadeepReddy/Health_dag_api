cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "nlp_bert_in_graph_batch2_fix.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_bertfix.py"
dst = dev / "nlp_bert_in_graph_batch2_qkvfix.py"
newgraph = dev / "grecbase_fusion_full_head_72_max_batch2_bertqkvfix.py"

assert src.is_file() and graph.is_file(), "STOP: Known source missing"

code = src.read_text()
tree = ast.parse(code)
lines = code.splitlines(keepends=True)
edits = []
fixed = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Call) or len(n.args) < 2:
        continue
    if not isinstance(n.func, ast.Attribute):
        continue
    if not (isinstance(n.func.value, ast.Name)
            and n.func.value.id == "ops"
            and n.func.attr == "reshape"):
        continue

    value, shape = n.args[:2]
    if not isinstance(value, ast.Name) or value.id not in ("q", "k", "v"):
        continue
    if not isinstance(shape, ast.List) or len(shape.elts) != 4:
        continue

    parts = shape.elts
    if not (
        isinstance(parts[0], ast.Constant) and parts[0].value == 1
        and isinstance(parts[1], ast.Name) and parts[1].id == "seq_len"
        and isinstance(parts[2], ast.Constant) and parts[2].value == 12
        and isinstance(parts[3], ast.Constant) and parts[3].value == 32
    ):
        continue

    start = sum(map(len, lines[:shape.lineno-1])) + shape.col_offset
    end = sum(map(len, lines[:shape.end_lineno-1])) + shape.end_col_offset
    edits.append((start, end, "[2, seq_len, 12, 32]"))
    fixed.append((value.id, n.lineno))

assert sum(name == "q" for name, _ in fixed) == 1, \
    f"STOP: Expected exactly one Q reshape: {fixed}"

updated = code
for start, end, replacement in sorted(edits, reverse=True):
    updated = updated[:start] + replacement + updated[end:]

ast.parse(updated)

graph_code = graph.read_text()
old = "from nlp_bert_in_graph_batch2_fix import "
new = "from nlp_bert_in_graph_batch2_qkvfix import "
assert graph_code.count(old) == 1, "STOP: BERT graph import differs"
graph_code = graph_code.replace(old, new, 1)
ast.parse(graph_code)

for path, content in ((dst, updated), (newgraph, graph_code)):
    if path.exists():
        assert path.read_text() == content, f"STOP: Existing candidate differs: {path}"
        print("VERIFIED:", path.name)
    else:
        path.write_text(content)
        print("CREATED:", path.name)

print("BERT ATTENTION FIXES:", fixed)
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS AND WORKING RELEASE: UNCHANGED")
PY

echo "=== REBUILD REAL BATCH-2 GRAPH ==="

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
    from grecbase_fusion_full_head_72_max_batch2_bertqkvfix import (
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

print("REAL BATCH-2 EXECUTION: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
