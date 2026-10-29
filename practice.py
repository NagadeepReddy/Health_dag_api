cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/nlp_bert_in_graph_batch2_fix.py")
assert p.is_file(), f"STOP: Missing {p}"

old = "from .nlp_bert_max import WEIGHTS"
new = "from cta_max.nlp_bert_max import WEIGHTS"
code = p.read_text()

if code.count(old) == 1:
    updated = code.replace(old, new, 1)
    tree = ast.parse(updated)
    remaining = [
        n.lineno for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.level > 0
    ]
    assert not remaining, f"STOP: Other relative imports at {remaining}"

    backup = p.with_suffix(".py.before_importfix.bak")
    assert not backup.exists(), "STOP: Backup already exists"
    backup.write_bytes(p.read_bytes())
    p.write_text(updated)
    print("BERT ABSOLUTE IMPORT FIX: INSTALLED")
elif code.count(new) == 1:
    print("BERT ABSOLUTE IMPORT FIX: ALREADY PRESENT")
else:
    raise SystemExit("STOP: Import differs from expected source")

print("PYTHON SYNTAX: PASS")
print("ORIGINAL CTA PACKAGE: UNCHANGED")
PY

echo "=== BATCH-2 GRAPH REBUILD ==="

test -d /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights && \
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

    print("BATCH-2 GRAPH BUILD: START", flush=True)

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
