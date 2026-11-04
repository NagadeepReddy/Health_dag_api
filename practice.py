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

print("=== PZAAS WEIGHT ALIAS FIX + FULL PARITY ===", flush=True)

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
        shape = tuple(int(x) for x in entry.weight.shape)

        alias = re.sub(
            r"(sequence_transformer\.ptransformer\.[01])\.(?!fn\.)",
            r"\1.fn.",
            name
        )

        candidates = list(dict.fromkeys([name, alias]))
        arr = None
        errors = []

        for candidate in candidates:
            try:
                value = np.asarray(
                    loader.load_weight(candidate, shape)
                )
                if value.shape != shape:
                    raise ValueError(
                        f"{value.shape} != {shape}"
                    )
                arr = np.ascontiguousarray(value)
                if candidate != name:
                    print("ALIAS:", name, "<-", candidate)
                break
            except Exception as exc:
                errors.append(
                    f"{candidate}: {type(exc).__name__}: {exc}"
                )

        if arr is None:
            missing.append((name, errors))
        else:
            registry[name] = arr

    print("GRAPH WEIGHTS:", len(graph._weights))
    print("BOUND WEIGHTS:", len(registry))
    print("MISSING WEIGHTS:", len(missing))

    if missing:
        for name, errors in missing:
            print("MISSING:", name)
            for error in errors:
                print(" ", error[:180])
        raise RuntimeError("Weight binding incomplete")

    assert len(registry) == 17
    print("ALL 17 WEIGHTS: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph,
        weights_registry=registry
    )
    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    folder = Path(
        "artifacts/v1.472-max/pzaas_max/validation"
    )
    input_path = folder / "ppa_tensor_inputs.npz"
    ref_path = folder / "ppa_pytorch_reference_01.pt"

    with np.load(input_path, allow_pickle=False) as data:
        keys = list(data.files)

        def index(key):
            match = re.fullmatch(
                r"(?:arr_|input_|tensor_)?(\d+)", key
            )
            return int(match.group(1)) if match else None

        indices = [index(key) for key in keys]

        if (
            len(keys) != len(graph.inputs)
            or any(x is None for x in indices)
            or sorted(indices) != list(range(len(keys)))
        ):
            raise RuntimeError(
                "Saved input order not verified: "
                + str(keys[:12])
            )

        inputs = [
            np.ascontiguousarray(data[key])
            for key in sorted(keys, key=index)
        ]

    print("INPUT MAPPING: PASS", flush=True)

    outputs = model.execute(*inputs)
    assert len(outputs) == 1

    actual = outputs[0].to_numpy()
    print("MAX EXECUTION: PASS", flush=True)

    reference = torch.load(
        ref_path,
        map_location="cpu",
        weights_only=True
    )

    def find_tensors(value):
        if isinstance(value, torch.Tensor):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from find_tensors(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from find_tensors(child)

    candidates = [
        tensor for tensor in find_tensors(reference)
        if tuple(tensor.shape) == tuple(actual.shape)
    ]

    if len(candidates) != 1:
        raise RuntimeError(
            "Reference output not uniquely identified: "
            + str(len(candidates))
        )

    expected = candidates[0].detach().cpu().numpy()

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected,
        rtol=1e-3,
        atol=1e-3
    )

    print("OUTPUT SHAPE:", actual.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print(
        "FULL NUMERICAL PARITY:",
        "PASS" if passed else "FAIL"
    )

except Exception as exc:
    print("RETEST: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=3)

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
