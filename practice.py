cd /application1/sajjna8/rt-pzaas-v1.0 && \
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

print("=== PZAAS REAL MAX GRAPH BUILD ===", flush=True)

try:
    from pzaas_max.grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )

    device = DeviceRef.CPU()
    graph = build_grecbase_fusion_graph_order_correct(device)

    print("PZAAS MAX GRAPH BUILD: PASS", flush=True)
    print("DEVICE: CPU")
    print("GRAPH TYPE:", type(graph).__name__)
    print("MAX COMPILATION: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX GRAPH BUILD: FAILED")
PY
