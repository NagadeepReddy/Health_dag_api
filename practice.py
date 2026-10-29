cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "nlp_bert_in_graph_batch2_qkvfix.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_bertqkvfix.py"

dst = dev / "nlp_bert_in_graph_batch2_contextfix.py"
newgraph = dev / "grecbase_fusion_full_head_72_max_batch2_bertcontextfix.py"

assert src.is_file() and graph.is_file(), "STOP: Previous verified files missing"

code = src.read_text()
tree = ast.parse(code)
matches = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "context" for t in n.targets):
        continue
    call = n.value
    if not isinstance(call, ast.Call) or len(call.args) < 2:
        continue
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "reshape":
        continue
    if ast.unparse(call.args[1]) == "[1, seq_len, 384]":
        matches.append(call.args[1])

assert len(matches) == 1, f"STOP: Expected one context reshape, found {len(matches)}"

shape = matches[0]
lines = code.splitlines(keepends=True)
start = sum(len(x) for x in lines[:shape.lineno-1]) + shape.col_offset
end = sum(len(x) for x in lines[:shape.end_lineno-1]) + shape.end_col_offset

updated = code[:start] + "[2, seq_len, 384]" + code[end:]
ast.parse(updated)

graph_code = graph.read_text()
old = "from nlp_bert_in_graph_batch2_qkvfix import"
new = "from nlp_bert_in_graph_batch2_contextfix import"

assert graph_code.count(old) == 1, "STOP: Graph import differs"
graph_code = graph_code.replace(old, new, 1)
ast.parse(graph_code)

for p, content in ((dst, updated), (newgraph, graph_code)):
    if p.exists():
        assert p.read_text() == content, f"STOP: Existing file differs: {p}"
        print("VERIFIED:", p.name)
    else:
        p.write_text(content)
        print("CREATED:", p.name)

print("BERT CONTEXT RESHAPE: [1,seq_len,384] -> [2,seq_len,384]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY

echo "=== REAL BATCH-2 GRAPH REBUILD ==="

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
import sys
import traceback

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_bertcontextfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    print("REAL BATCH-2 GRAPH BUILD: START", flush=True)
    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))

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
