cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
-e PYTHONPATH=/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import importlib, traceback, re
from pathlib import Path
import numpy as np
import torch
from max.driver import CPU
from max.engine import InferenceSession
from max.graph import DeviceRef

print("=== PZAAS CORRECTED WEIGHT BINDING + PARITY ===", flush=True)

try:
    mod = importlib.import_module(
        "pzaas_max.grecbase_fusion_full_head_72_max"
    )
    loader = importlib.import_module(
        "pzaas_max.pzaas_weight_loader"
    )

    graph = mod.build_grecbase_fusion_graph_order_correct(
        DeviceRef.CPU()
    )
    print("MAX GRAPH: PASS", flush=True)

    registry = {}
    missing = []

    for name, entry in graph._weights.items():
        weight = entry.weight
        shape = tuple(int(d) for d in weight.shape)

        arr = None
        for candidate in (name, name + ".weight", name + ".g"):
            try:
                value = loader.load_weight(candidate, shape)
                value = np.ascontiguousarray(value)
                if value.shape == shape:
                    arr = value
                    break
            except (KeyError, ValueError, FileNotFoundError):
                continue

        if arr is None:
            missing.append((name, shape))
        else:
            registry[name] = arr

    print("GRAPH WEIGHTS:", len(graph._weights))
    print("WEIGHTS BOUND:", len(registry))
    print("MISSING:", missing[:10])

    if missing:
        raise RuntimeError("Weight binding incomplete")

    print("WEIGHT BINDING: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph, weights_registry=registry
    )
    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    folder = Path("artifacts/v1.472-max/pzaas_max/validation")
    input_path = folder / "ppa_tensor_inputs.npz"
    reference_path = folder / "ppa_pytorch_reference_01.pt"

    with np.load(input_path, allow_pickle=False) as data:
        keys = list(data.files)

        def idx(k):
            match = re.fullmatch(
                r"(?:arr_|input_|tensor_)?(\d+)", k
            )
            return int(match.group(1)) if match else None

        indices = [idx(k) for k in keys]
        if (
            len(keys) != len(graph.inputs)
            or any(i is None for i in indices)
            or sorted(indices) != list(range(len(keys)))
        ):
            raise RuntimeError(
                f"Input order needs verification: {keys[:10]}"
            )

        inputs = [
            np.ascontiguousarray(data[k])
            for k in sorted(keys, key=idx)
        ]

    print("INPUT MAPPING: PASS", flush=True)

    result = model.execute(*inputs)
    if len(result) != 1:
        raise RuntimeError("Unexpected MAX output count")

    actual = result[0].to_numpy()

    ref = torch.load(
        reference_path,
        map_location="cpu",
        weights_only=True
    )

    if isinstance(ref, dict):
        candidates = [
            v for v in ref.values()
            if isinstance(v, torch.Tensor)
            and tuple(v.shape) == tuple(actual.shape)
        ]
        if len(candidates) != 1:
            raise RuntimeError("Reference output ambiguous")
        ref = candidates[0]

    expected = ref.detach().cpu().numpy()

    if actual.shape != expected.shape:
        raise RuntimeError(
            f"Shape mismatch: {actual.shape} vs {expected.shape}"
        )

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, atol=1e-3, rtol=1e-3
    )

    print("OUTPUT SHAPE:", actual.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("FULL NUMERICAL PARITY:",
          "PASS" if passed else "FAIL")

except Exception as exc:
    print("RETEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=3)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
