cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472-max \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local -u - <<'PY'
import traceback
from max.graph import DeviceRef
from max.driver import CPU
from max.engine import InferenceSession

print("=== PZAAS MAX CPU COMPILATION ===", flush=True)

try:
    from pzaas_max.grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )

    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.CPU()
    )
    print("PZAAS GRAPH BUILD: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])

    if not callable(getattr(session, "load", None)):
        raise RuntimeError(
            "Installed MAX session has no load() API"
        )

    print("STARTING MAX CPU COMPILATION", flush=True)
    model = session.load(graph)

    print("PZAAS MAX CPU COMPILATION: PASS", flush=True)
    print("MODEL TYPE:", type(model).__name__)
    print("DEVICE: CPU")
    print("MODEL: PZAAS v1.472")
    print("INFERENCE: PENDING")
    print("PARITY: PENDING")
    print("NATIVE HTTP: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX CPU COMPILATION: FAILED")
PY
