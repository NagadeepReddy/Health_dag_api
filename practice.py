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
import importlib.util
import json
import re
import traceback
from pathlib import Path

import numpy as np
import torch
from max.driver import CPU
from max.engine import InferenceSession
from max.graph import DeviceRef

root = Path("artifacts/v1.472-max/pzaas_max")
validation = root / "validation"

print("=== PZAAS NATIVE MAX NUMERICAL PARITY ===", flush=True)

try:
    schema = json.loads(
        (validation / "pzaas_forward_schema.json").read_text()
    )

    spec = importlib.util.spec_from_file_location(
        "pzaas_input_adapter",
        validation / "pzaas_forward_input_adapter.py"
    )
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)

    assert callable(adapter.pack)

    model_input = torch.load(
        validation / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=True
    )

    print("SAVED EXACT INPUT: READ")

    if isinstance(model_input, dict):
        print("INPUT GROUPS:", list(model_input.keys())[:25])

    packed = adapter.pack(model_input)

    if isinstance(packed, dict) and "inputs" in packed:
        packed = packed["inputs"]

    if not isinstance(packed, (list, tuple)):
        raise TypeError(
            f"Unexpected adapter output: {type(packed).__name__}"
        )

    inputs = []
    for item in packed:
        if isinstance(item, torch.Tensor):
            item = item.detach().cpu().numpy()
        elif not isinstance(item, np.ndarray):
            raise TypeError(
                f"Unsupported packed input: {type(item).__name__}"
            )
        inputs.append(np.ascontiguousarray(item))

    print("SCHEMA GROUPS:",
          len(schema.get("forward_arguments", [])))
    print("PACKED TENSORS:", len(inputs))

    graph_module = importlib.import_module(
        "pzaas_max.grecbase_fusion_full_head_72_max"
    )
    loader = importlib.import_module(
        "pzaas_max.pzaas_weight_loader"
    )

    graph = graph_module.build_grecbase_fusion_graph_order_correct(
        DeviceRef.CPU()
    )

    print("MAX GRAPH: PASS")
    print("GRAPH INPUTS:", len(graph.inputs))

    if len(inputs) != len(graph.inputs):
        raise RuntimeError(
            f"Input count mismatch: {len(inputs)} vs "
            f"{len(graph.inputs)}"
        )

    print("EXACT INPUT MAPPING: PASS", flush=True)

    weights = {}
    missing = []

    for name, entry in graph._weights.items():
        shape = tuple(int(d) for d in entry.weight.shape)

        fn_name = re.sub(
            r"(sequence_transformer\.ptransformer\.[01])\.(?!fn\.)",
            r"\1.fn.",
            name
        )

        candidates = dict.fromkeys([
            name,
            name + ".weight",
            fn_name,
            fn_name + ".weight"
        ])

        found = False

        for candidate in candidates:
            try:
                arr = np.asarray(
                    loader.load_weight(candidate, shape)
                )

                if tuple(arr.shape) != shape:
                    continue

                weights[name] = np.ascontiguousarray(arr)
                found = True
                break

            except (KeyError, ValueError, FileNotFoundError):
                continue

        if not found:
            missing.append(name)

    print("GRAPH WEIGHTS:", len(graph._weights))
    print("BOUND WEIGHTS:", len(weights))

    if missing:
        raise RuntimeError(f"Missing weights: {missing}")

    assert len(weights) == 17

    print("ALL 17 WEIGHTS: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(graph, weights_registry=weights)

    print("MAX CPU COMPILATION: PASS", flush=True)

    outputs = model.execute(*inputs)
    if len(outputs) != 1:
        raise RuntimeError(
            f"Expected one graph output, got {len(outputs)}"
        )

    actual = outputs[0].to_numpy()

    print("REAL MAX EXECUTION: PASS")
    print("MAX OUTPUT SHAPE:", actual.shape)

    reference = torch.load(
        validation / "ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )

    def collect(obj):
        if isinstance(obj, torch.Tensor):
            yield obj.detach().cpu().numpy()
        elif isinstance(obj, np.ndarray):
            yield obj
        elif isinstance(obj, dict):
            for value in obj.values():
                yield from collect(value)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                yield from collect(value)

    matches = [
        x for x in collect(reference)
        if x.shape == actual.shape
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one matching reference output; "
            f"found {len(matches)}"
        )

    expected = matches[0]

    if not (
        np.isfinite(actual).all()
        and np.isfinite(expected).all()
    ):
        raise RuntimeError("Non-finite numerical output")

    diff = np.abs(actual - expected)

    passed = np.allclose(
        actual, expected,
        rtol=1e-3,
        atol=1e-3
    )

    print("PYTORCH SHAPE:", expected.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("NUMERICAL PARITY:",
          "PASS" if passed else "FAIL")

    if not passed:
        raise RuntimeError("Numerical parity not achieved")

    print("PZAAS FULL NUMERICAL PARITY: PASS")
    print("NEXT: NATIVE MAX SERVE HTTP")

except Exception as exc:
    print("PZAAS TEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
