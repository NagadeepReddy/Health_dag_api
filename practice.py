cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = Path("artifacts/v1.168-max/cta_max/nlp_bert_in_graph.py")
graph = dev / "grecbase_fusion_full_head_72_max_batch2_siblingfix.py"

fixed = dev / "nlp_bert_in_graph_batch2_fix.py"
newgraph = dev / "grecbase_fusion_full_head_72_max_batch2_bertfix.py"

assert src.is_file() and graph.is_file(), "STOP: Source missing"

code = src.read_text()
tree = ast.parse(code)
matches = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Call) or len(n.args) < 2:
        continue
    if not isinstance(n.func, ast.Attribute) or n.func.attr != "reshape":
        continue

    if "attention_mask" not in ast.unparse(n.args[0]):
        continue

    if ast.unparse(n.args[1]) == "[1, 1, 1, seq_len]":
        matches.append(n.args[1])

assert len(matches) == 1, \
    f"STOP: Expected one attention-mask reshape; found {len(matches)}"

node = matches[0]
lines = code.splitlines(keepends=True)
start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset

fixed_code = code[:start] + "[2, 1, 1, seq_len]" + code[end:]
ast.parse(fixed_code)

graph_tree = ast.parse(graph.read_text())
imports = [
    n for n in ast.walk(graph_tree)
    if isinstance(n, ast.ImportFrom)
    and n.module == "cta_max.nlp_bert_in_graph"
]
assert len(imports) == 1, \
    f"STOP: Expected one BERT import, found {len(imports)}"

imports[0].module = "nlp_bert_in_graph_batch2_fix"
ast.fix_missing_locations(graph_tree)
graph_code = ast.unparse(graph_tree) + "\n"
ast.parse(graph_code)

for path, content in (
    (fixed, fixed_code),
    (newgraph, graph_code)
):
    if path.exists():
        assert path.read_text() == content, \
            f"STOP: Existing file differs: {path}"
        print("VERIFIED:", path.name)
    else:
        path.write_text(content)
        print("CREATED:", path.name)

print("BATCH-2 ATTENTION MASK FIX: INSTALLED")
print("SHAPE: [1,1,1,seq_len] -> [2,1,1,seq_len]")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS AND MAX FILES: UNCHANGED")
PY

echo "=== RETRY REAL BATCH-2 GRAPH BUILD ==="

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
    from grecbase_fusion_full_head_72_max_batch2_bertfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

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

print("REAL BATCH-2 EXECUTION: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
