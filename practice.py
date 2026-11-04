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
import json
import traceback
from pathlib import Path
import numpy as np

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
    print("GRAPH BUILD: PASS", flush=True)

    root = Path(
        "/workspace/artifacts/v1.472-max/pzaas_max/pzaas_base_weights"
    )
    manifest = json.loads(
        (root / "manifest.json").read_text()
    )

    registry = {}
    missing = []

    required = list(graph._weights.keys())
    print("GRAPH WEIGHTS REQUIRED:", len(required), flush=True)

    for name in required:
        key = name if name in manifest else name + ".weight"

        if key not in manifest:
            missing.append(name)
            continue

        entry = manifest[key]
        path = root / entry["file"]

        array = np.array(
            np.load(path, allow_pickle=False, mmap_mode="r"),
            copy=True,
            order="C"
        )

        if tuple(array.shape) != tuple(entry["shape"]):
            raise ValueError(f"Shape mismatch: {key}")

        registry[name] = array
        print("REGISTERED:", name, array.shape, flush=True)

    if missing:
        raise ValueError(f"Unmapped MAX weights: {missing}")

    print("WEIGHTS REGISTRY: PASS", flush=True)
    print("STARTING REAL CPU COMPILATION", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(graph, weights_registry=registry)

    print("PZAAS MAX CPU COMPILATION: PASS", flush=True)
    print("MODEL TYPE:", type(model).__name__)
    print("DEVICE: CPU")
    print("ORIGINAL DS: UNCHANGED")
    print("INFERENCE / PARITY: PENDING")
    print("NATIVE HTTP: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX CPU COMPILATION: FAILED")
PY
