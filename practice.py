cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
GRAPH=grecbase_fusion_full_head_72_max_batch2_auxfix

test -f "$DEV/$GRAPH.py"

WEIGHT=$(find \
  "$REPO/artifacts/v1.168-max" \
  /application1/cta_max_true_batch_dev_20261028 \
  "$DEV" \
  -type f -name 'task_embedding.0.weight.npy' \
  -print -quit 2>/dev/null || true)

if [ -z "$WEIGHT" ]; then
  echo "STOP: Exact auxiliary trained weight not located"
  echo "=== AVAILABLE AUXILIARY WEIGHT FILES ==="
  find "$REPO/artifacts/v1.168-max" \
    /application1/cta_max_true_batch_dev_20261028 \
    -type f \( -iname '*task*embedding*.npy' -o -iname '*aux*weight*.npy' \) \
    -print 2>/dev/null | head -30
  echo "GRAPH BUILD: NOT RETRIED"
  exit 1
fi

SOURCE=$(dirname "$WEIGHT")
echo "AUXILIARY TRAINED WEIGHTS: FOUND"
echo "SOURCE: $SOURCE"

python3 -S -B - "$SOURCE" "$DEV" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
dev = Path(sys.argv[2])
dest = dev / "grecbase_aux_weights"

assert source.is_dir()
assert (source / "task_embedding.0.weight.npy").is_file()

if dest.is_symlink():
    assert dest.readlink() == Path("/weights_aux"), \
        "STOP: Existing auxiliary link differs"
elif dest.exists():
    assert dest.is_dir(), "STOP: Unexpected auxiliary destination"
    for original in source.glob("*.npy"):
        link = dest / original.name
        expected = Path("/weights_aux") / original.name
        if link.is_symlink():
            assert link.readlink() == expected, \
                f"STOP: Conflicting link {link}"
        elif link.exists():
            raise SystemExit(f"STOP: Existing file needs review: {link}")
        else:
            link.symlink_to(expected)
else:
    dest.symlink_to("/weights_aux")

print("AUXILIARY WEIGHT MAPPING: READY")
print("ORIGINAL TRAINED WEIGHTS: UNCHANGED")
PY

echo "=== TRUE BATCH-2 GRAPH REBUILD ==="

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
  -v "$SOURCE:/weights_aux:ro" \
  -v "$REPO/artifacts/v1.168-max/cta_max/main_context_weights:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

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

    for i, value in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", value.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
