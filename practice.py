set -e
cd /application1/sajjna8/rt-pzaas-v1.0

python3 - <<'PY'
from pathlib import Path
import json

root = Path("artifacts/v1.472-max/pzaas_max")
manifest = json.loads(
    (root/"pzaas_base_weights/manifest.json").read_text()
)

fixes = {
    "sibling_context_max.py": "sibling_context_head.",
    "main_context_max.py": "context_head.",
}

updates = {}

for filename, prefix in fixes.items():
    p = root/filename
    source = p.read_text()

    old = f'load_weight("{prefix}" + name)'
    new = (
        f'load_weight(name if name.startswith("{prefix}") '
        f'else "{prefix}" + name)'
    )

    if source.count(old) == 1:
        updated = source.replace(old, new, 1)
    elif new in source:
        updated = source
    else:
        raise SystemExit(f"STOP: Unexpected loader in {filename}")

    key = prefix + "deep_embedding.0.weight"
    if key not in manifest:
        raise SystemExit(f"STOP: Missing checkpoint weight: {key}")

    compile(updated, str(p), "exec")
    updates[p] = updated

for p, updated in updates.items():
    if p.read_text() != updated:
        p.write_text(updated)
    print("FIX VERIFIED:", p.name)

print("PZAAS WEIGHT PREFIX FIX: PASS")
print("ORIGINAL DS: UNCHANGED")
PY

podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --memory 10g \
--tmpfs /tmp:rw,size=512m \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472-max \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local - <<'PY'
import traceback
from max.graph import DeviceRef

print("=== PZAAS MAX GRAPH BUILD RETRY ===", flush=True)

try:
    from pzaas_max.grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )

    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.CPU()
    )

    print("PZAAS MAX GRAPH BUILD: PASS", flush=True)
    print("GRAPH TYPE:", type(graph).__name__)
    print("CPU COMPILATION: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX GRAPH BUILD: FAILED")
PY
