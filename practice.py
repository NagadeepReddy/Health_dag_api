set -eu

REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029

python3 -S -B - <<'PY'
from pathlib import Path
import os
import hashlib

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
name = "sibling_context_head_deep_embedding_0.weight.npy"
destination = dev / "sibling_context_weights"

assert repo.is_dir() and dev.is_dir(), "STOP: Project or development directory missing"

matches = sorted(
    p for base in (repo / "artifacts", dev)
    for p in base.rglob(name)
    if p.is_file()
)

print("SIBLING WEIGHT CANDIDATES:", len(matches))
for p in matches:
    print("FOUND:", p)

assert matches, "STOP: Existing trained sibling weight not found"

digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in matches}
assert len(digests) == 1, "STOP: Conflicting sibling weight files found"

source = matches[0].parent.resolve()

if source.is_relative_to(repo):
    target = "/workspace/" + str(source.relative_to(repo))
elif source.is_relative_to(dev):
    target = "/batch2/" + str(source.relative_to(dev))
else:
    raise SystemExit("STOP: Weight source outside mounted directories")

assert source != destination.resolve(), "STOP: Unexpected self-reference"

if destination.is_symlink():
    assert os.readlink(destination) == target, "STOP: Existing link differs"
    print("SIBLING WEIGHT LINK: ALREADY CORRECT")
elif destination.exists():
    raise SystemExit("STOP: Existing sibling weight directory; refusing overwrite")
else:
    destination.symlink_to(target, target_is_directory=True)
    print("SIBLING WEIGHT LINK: CREATED")

print("WEIGHT SOURCE:", source)
print("WEIGHT TARGET IN CONTAINER:", target)
print("ORIGINAL WEIGHTS: UNCHANGED")
print("DS CODE: UNCHANGED")
PY

echo "=== RETEST BATCH-2 GRAPH ==="

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
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_siblingfix import (
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

print("REAL BATCH-2 EXECUTION: NOT YET PERFORMED")
print("WORKING RELEASE: UNCHANGED")
PY
