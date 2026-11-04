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
import inspect
import re
import traceback
import numpy as np
import torch
from pathlib import Path
from max.driver import CPU
from max.engine import InferenceSession
from max.graph import DeviceRef

print("=== PZAAS WEIGHT BINDING + PARITY ===", flush=True)

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

    graph_weights = getattr(graph, "_weights", None)
    if not graph_weights:
        raise RuntimeError("Graph weight metadata unavailable")

    registry = {}
    retained = []
    failures = []

    for name, weight in graph_weights.items():
        shape = tuple(int(x) for x in weight.shape)
        candidates = [name]
        if not name.endswith(".weight"):
            candidates.append(name + ".weight")

        loaded = None
        errors = []

        for candidate in candidates:
            try:
                try:
                    arr = loader.load_weight(candidate, shape)
                except TypeError:
                    if len(inspect.signature(
                        loader.load_weight
                    ).parameters) == 1:
                        arr = loader.load_weight(candidate)
                    else:
                        raise

                arr = np.asarray(arr)

                if tuple(arr.shape) != shape:
                    raise ValueError(
                        f"shape {arr.shape}, expected {shape}"
                    )

                loaded = np.ascontiguousarray(arr)
                break

            except Exception as exc:
                errors.append(
                    f"{candidate}: {type(exc).__name__}: {exc}"
                )

        if loaded is None:
            failures.append((name, errors))
        else:
            retained.append(loaded)
            registry[name] = loaded

    print("GRAPH WEIGHTS:", len(graph_weights))
    print("BOUND WEIGHTS:", len(registry))
    print("MISSING WEIGHTS:", len(failures))

    if failures:
        for name, errors in failures[:10]:
            print("UNRESOLVED:", name)
            for error in errors:
                print(" ", error[:180])
        raise RuntimeError("Incomplete weight binding")

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph, weights_registry=registry
    )
    print("MAX CPU COMPILATION + WEIGHT BINDING: PASS",
          flush=True)

    folder = Path("artifacts/v1.472-max/pzaas_max/validation")
    input_file = folder / "ppa_tensor_inputs.npz"
    reference_file = folder / "ppa_pytorch_reference_01.pt"

    if not input_file.is_file() or not reference_file.is_file():
        raise RuntimeError("Saved parity references unavailable")

    with np.load(input_file, allow_pickle=False) as data:
        keys = list(data.files)

        def number(key):
            match = re.fullmatch(
                r"(?:arr_|input_|tensor_)?(\d+)", key
            )
            return int(match.group(1)) if match else None

        indices = [number(k) for k in keys]
        expected_count = len(graph.inputs)

        if (
            len(keys) != expected_count
            or any(i is None for i in indices)
            or sorted(indices) != list(range(expected_count))
        ):
            raise RuntimeError(
                f"Input order not verified: "
                f"{len(keys)} saved, "
                f"{expected_count} expected; "
                f"first keys={keys[:8]}"
            )

        inputs = [
            np.ascontiguousarray(data[k])
            for k in sorted(keys, key=number)
        ]

    print("INPUT MAPPING: PASS", flush=True)

    outputs = model.execute(*inputs)
    if len(outputs) != 1:
        raise RuntimeError("Unexpected number of MAX outputs")

    actual = outputs[0].to_numpy()

    ref = torch.load(
        reference_file,
        map_location="cpu",
        weights_only=True
    )

    if isinstance(ref, dict):
        matches = [
            value for value in ref.values()
            if isinstance(value, torch.Tensor)
            and tuple(value.shape) == tuple(actual.shape)
        ]
        if len(matches) != 1:
            raise RuntimeError(
                "Reference output not uniquely identified"
            )
        ref = matches[0]

    if not isinstance(ref, torch.Tensor):
        raise RuntimeError("Unsupported reference output")

    expected = ref.detach().cpu().numpy()

    assert actual.shape == expected.shape, (
        f"Shape mismatch: {actual.shape} vs {expected.shape}"
    )

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    )

    print("OUTPUT SHAPE:", actual.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("NUMERICAL PARITY:",
          "PASS" if passed else "FAIL")

except Exception as exc:
    print("RETEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=3)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
