REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" \
  -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import traceback
from pathlib import Path

dev = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev").resolve()
sys.path.insert(0, str(dev))

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct

    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.from_device(CPU())
    )

    print("BPLAN MAX GRAPH BUILD: PASS")
    print("INPUTS:", len(graph.inputs))
except Exception:
    print("BPLAN MAX GRAPH BUILD: FAILED")
    traceback.print_exc()
    raise SystemExit(1)
PY
