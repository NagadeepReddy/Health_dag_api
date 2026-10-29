cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
WEIGHTS="$REPO/artifacts/v1.168-max/cta_max/main_context_weights"
ALIAS="$DEV/main_context_weights"

test -f "$DEV/grecbase_fusion_full_head_72_max_batch2_mainfix.py"
test -d "$WEIGHTS"

python3 -S -B - "$WEIGHTS" "$ALIAS" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

assert not dst.is_symlink(), "STOP: Existing directory link needs review"
assert not dst.exists() or dst.is_dir(), "STOP: Invalid destination"

# The real exports use deep_embedding.0, deep_embedding.1, etc.
# Our development graph requests deep_embedding_0, deep_embedding_1.
for i in range(17):
    original = src / f"context_head.deep_embedding.{i}.weight.npy"
    assert original.is_file(), f"STOP: Missing trained weight {original}"

dst.mkdir(exist_ok=True)

count = 0
for original in sorted(src.glob("*.npy")):
    names = {original.name}
    if ".deep_embedding." in original.name:
        names.add(original.name.replace(".deep_embedding.", ".deep_embedding_", 1))

    for name in names:
        link = dst / name
        target = Path("/weights_main") / original.name

        if link.is_symlink():
            assert link.readlink() == target, f"STOP: Different link: {link}"
        elif link.exists():
            raise SystemExit(f"STOP: Refusing overwrite: {link}")
        else:
            link.symlink_to(target)
        count += 1

print("TRAINED EMBEDDING WEIGHTS: 17/17 FOUND")
print("MAIN-CONTEXT WEIGHT LINKS:", count)
print("ORIGINAL WEIGHTS: UNCHANGED")
print("DS CODE: UNCHANGED")
PY

echo "=== RETRY REAL BATCH-2 GRAPH ==="

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
  -v "$WEIGHTS:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_mainfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    print("REAL BATCH-2 GRAPH BUILD: START", flush=True)
    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))
    for i, value in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", value.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
