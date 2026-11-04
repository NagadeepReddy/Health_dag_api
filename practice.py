cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
-e PYTHONPATH=/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import importlib
import re
import traceback
from pathlib import Path

import numpy as np
import torch
from max.driver import CPU
from max.engine import InferenceSession
from max.graph import DeviceRef

print("=== PZAAS TWO-LAYER REAL MAX RETEST ===", flush=True)

base = Path("artifacts/v1.472-max/pzaas_max")
validation = base / "validation"

try:
    mod = importlib.import_module(
        "pzaas_max.grecbase_fusion_full_head_72_max"
    )

    builder = getattr(
        mod, "build_grecbase_fusion_graph_order_correct",
        None
    )
    if not callable(builder):
        raise RuntimeError(
            "Exact MAX graph builder unavailable"
        )

    graph = builder(DeviceRef.CPU())
    print("MAX GRAPH BUILD: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(graph)
    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    input_file = validation / "ppa_tensor_inputs.npz"
    ref_file = validation / "ppa_pytorch_reference_01.pt"

    if not input_file.is_file() or not ref_file.is_file():
        raise RuntimeError(
            "Saved input or PyTorch reference missing"
        )

    with np.load(input_file, allow_pickle=False) as saved:
        keys = list(saved.files)
        count = len(graph.inputs)

        def index_key(k):
            m = re.fullmatch(
                r"(?:arr_|input_|tensor_)([0-9]+)", k
            )
            return int(m.group(1)) if m else None

        indexes = [index_key(k) for k in keys]
        if (
            len(keys) != count
            or any(i is None for i in indexes)
            or sorted(indexes) != list(range(count))
        ):
            raise RuntimeError(
                f"Input mapping unverified: "
                f"{len(keys)} saved arrays, "
                f"{count} graph inputs; "
                f"keys={keys[:8]}"
            )

        order = sorted(keys, key=index_key)
        inputs = [saved[k].copy() for k in order]

    print("EXACT INPUT ORDER: VERIFIED", flush=True)

    actual = model.execute(*inputs)
    if isinstance(actual, (tuple, list)):
        if len(actual) != 1:
            raise RuntimeError("Multiple MAX outputs")
        actual = actual[0]

    actual = (
        actual.to_numpy()
        if hasattr(actual, "to_numpy")
        else np.asarray(actual)
    )

    reference = torch.load(
        ref_file, map_location="cpu", weights_only=True
    )

    if isinstance(reference, dict):
        candidates = [
            v for v in reference.values()
            if isinstance(v, torch.Tensor)
            and tuple(v.shape) == tuple(actual.shape)
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                "PyTorch reference tensor ambiguous"
            )
        reference = candidates[0]

    if not isinstance(reference, torch.Tensor):
        raise RuntimeError("Unsupported reference format")

    expected = reference.detach().cpu().numpy()

    if actual.shape != expected.shape:
        raise RuntimeError(
            f"Shape mismatch: {actual.shape} vs {expected.shape}"
        )

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    )

    print("SHAPE:", actual.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("FULL NUMERICAL PARITY:",
          "PASS" if passed else "FAIL")

except Exception as exc:
    print("REAL MAX RETEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=3)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
