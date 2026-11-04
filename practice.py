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
import json, re, traceback
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
        "/workspace/artifacts/v1.472-max/"
        "pzaas_max/pzaas_base_weights"
    )
    manifest = json.loads(
        (root / "manifest.json").read_text()
    )

    registry = {}
    aliases = 0
    missing = []

    required = list(graph._weights.keys())
    print("REQUIRED GRAPH WEIGHTS:", len(required))

    for name in required:
        key = name

        if key not in manifest:
            match = re.fullmatch(
                r"(sequence_transformer\.ptransformer\.[01])\."
                r"(fused_attn_ff_proj|attn_out|ff_out\.1)\.weight",
                name
            )

            if match:
                key = (
                    match.group(1) + ".fn." +
                    match.group(2) + ".weight"
                )

        if key not in manifest:
            missing.append(name)
            continue

        entry = manifest[key]
        path = root / entry["file"]

        array = np.array(
            np.load(path, mmap_mode="r", allow_pickle=False),
            copy=True,
            order="C"
        )

        if tuple(array.shape) != tuple(entry["shape"]):
            raise ValueError(f"Shape mismatch: {key}")

        registry[name] = array

        if name != key:
            aliases += 1
            print("MAPPED:", name, "=>", key)
        else:
            print("REGISTERED:", name)

    if missing:
        raise ValueError(f"UNMAPPED WEIGHTS: {missing}")

    print("WEIGHTS REGISTRY: PASS")
    print("TRANSFORMER ALIASES:", aliases)

    if aliases != 6:
        raise ValueError(
            f"Expected 6 aliases, got {aliases}"
        )

    print("STARTING MAX CPU COMPILATION", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph,
        weights_registry=registry
    )

    print("PZAAS MAX CPU COMPILATION: PASS")
    print("MODEL TYPE:", type(model).__name__)
    print("MODEL: PZAAS v1.472")
    print("ORIGINAL DS: UNCHANGED")
    print("INFERENCE / PARITY: PENDING")
    print("NATIVE HTTP: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX CPU COMPILATION: FAILED")
PY
