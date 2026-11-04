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

print("=== PZAAS COMPLETE WEIGHT BINDING + PARITY ===", flush=True)

try:
    graph_module = importlib.import_module(
        "pzaas_max.grecbase_fusion_full_head_72_max"
    )
    loader = importlib.import_module(
        "pzaas_max.pzaas_weight_loader"
    )

    graph = graph_module.build_grecbase_fusion_graph_order_correct(
        DeviceRef.CPU()
    )
    print("MAX GRAPH: PASS", flush=True)

    registry = {}
    missing = []

    for name, entry in graph._weights.items():
        shape = tuple(int(d) for d in entry.weight.shape)

        fn_name = re.sub(
            r"(sequence_transformer\.ptransformer\.[01])\.(?!fn\.)",
            r"\1.fn.",
            name
        )

        candidates = list(dict.fromkeys([
            name,
            name + ".weight",
            fn_name,
            fn_name + ".weight"
        ]))

        found = False

        for candidate in candidates:
            try:
                array = np.asarray(
                    loader.load_weight(candidate, shape)
                )
                if tuple(array.shape) != shape:
                    continue

                registry[name] = np.ascontiguousarray(array)
                if candidate != name:
                    print("ALIAS:", name, "<-", candidate)
                found = True
                break

            except (KeyError, ValueError, FileNotFoundError):
                continue

        if not found:
            missing.append(name)

    print("GRAPH WEIGHTS:", len(graph._weights))
    print("BOUND WEIGHTS:", len(registry))
    print("MISSING:", missing)

    if missing:
        raise RuntimeError("Weight binding incomplete")

    assert len(registry) == 17
    print("ALL 17 WEIGHTS: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(graph, weights_registry=registry)
    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    folder = Path("artifacts/v1.472-max/pzaas_max/validation")
    input_file = folder / "ppa_tensor_inputs.npz"
    reference_file = folder / "ppa_pytorch_reference_01.pt"

    with np.load(input_file, allow_pickle=False) as data:
        keys = list(data.files)

        def input_index(key):
            match = re.fullmatch(
                r"(?:arr_|input_|tensor_)?(\d+)", key
            )
            return int(match.group(1)) if match else None

        indices = [input_index(k) for k in keys]

        if (
            len(keys) != len(graph.inputs)
            or any(i is None for i in indices)
            or sorted(indices) != list(range(len(keys)))
        ):
            raise RuntimeError(
                "Cannot verify saved input order: " + str(keys[:12])
            )

        inputs = [
            np.ascontiguousarray(data[k])
            for k in sorted(keys, key=input_index)
        ]

    print("INPUT MAPPING: PASS", flush=True)

    result = model.execute(*inputs)
    assert len(result) == 1

    actual = result[0].to_numpy()
    print("REAL MAX EXECUTION: PASS", flush=True)

    reference = torch.load(
        reference_file,
        map_location="cpu",
        weights_only=True
    )

    def tensors(obj):
        if isinstance(obj, torch.Tensor):
            yield obj
        elif isinstance(obj, dict):
            for value in obj.values():
                yield from tensors(value)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                yield from tensors(value)

    matches = [
        t for t in tensors(reference)
        if tuple(t.shape) == tuple(actual.shape)
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Reference output ambiguous: {len(matches)} matches"
        )

    expected = matches[0].detach().cpu().numpy()

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    )

    print("OUTPUT SHAPE:", actual.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("FULL NUMERICAL PARITY:", "PASS" if passed else "FAIL")

except Exception as exc:
    print("RETEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
