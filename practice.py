REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, traceback
from pathlib import Path

dev = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev").resolve()

# Temporary compatibility alias; BPLAN files only.
pkg = types.ModuleType("cta_max")
pkg.__path__ = [str(dev)]
sys.modules["cta_max"] = pkg
sys.path.insert(0, str(dev))

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from max.engine import InferenceSession
    device = CPU()

    from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct
    graph = build_grecbase_fusion_graph_order_correct(DeviceRef.from_device(device))

    assert len(graph.inputs) == 72
    print("BPLAN MAX GRAPH: PASS", flush=True)

    session = InferenceSession(devices=[device])
    model = session.load(graph)

    print("BPLAN MAX CPU COMPILE: PASS", flush=True)
except Exception:
    print("BPLAN MAX CPU COMPILE: FAILED", flush=True)
    traceback.print_exc()
    sys.exit(1)
PY
