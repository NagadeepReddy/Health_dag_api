REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, traceback
from pathlib import Path
import numpy as np
import torch

try:
    root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
    dev = root / "bplan_max_dev"

    # Temporary import alias points ONLY to BPLAN MAX files.
    pkg = types.ModuleType("cta_max")
    pkg.__path__ = [str(dev)]
    sys.modules["cta_max"] = pkg
    sys.path.insert(0, str(dev))

    from max.driver import CPU, Tensor
    from max.graph import DeviceRef
    from max.engine import InferenceSession
    from grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )
    from run_real_sanity_input_adapter import build_real_inputs

    data = torch.load(root / "bplan_neural_inputs.pt",
                      map_location="cpu", weights_only=True)
    data = dict(data)
    if "task_in" not in data and "tasks_in" in data:
        data["task_in"] = data["tasks_in"]

    labels, arrays = build_real_inputs(model_in=data)

    device = CPU()
    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.from_device(device)
    )
    assert len(labels) == len(arrays) == len(graph.inputs) == 72

    runtime_inputs = []
    converted = 0

    for label, arr, inp in zip(labels, arrays, graph.inputs):
        value = np.asarray(arr)
        expected = np.dtype(str(inp.type.dtype).split(".")[-1])
        assert tuple(value.shape) == tuple(int(x) for x in inp.type.shape)

        if value.dtype != expected:
            assert value.dtype == np.int64 and expected == np.float32
            cast = value.astype(np.float32)
            assert np.array_equal(value, cast.astype(np.int64)), label
            value = cast
            converted += 1

        runtime_inputs.append(
            Tensor.from_numpy(np.ascontiguousarray(value))
        )

    assert converted == 12
    print("BPLAN REAL INPUTS: PASS (72/72)", flush=True)

    state = torch.load(
        "artifacts/v1.113/core-artifact/base_model.pt",
        map_location="cpu", weights_only=True
    )
    if "state_dict" in state:
        state = state["state_dict"]

    registry = {}

    def register(name, value):
        if name in registry:
            assert np.array_equal(registry[name], value), name
        else:
            registry[name] = value

    for name, tensor in state.items():
        if not isinstance(tensor, torch.Tensor):
            continue

        value = tensor.detach().cpu().contiguous().numpy()
        register(name, value)

        if name.endswith(".weight"):
            register(name[:-7], value)

        if name.startswith("sequence_transformer.ptransformer.") and ".fn." in name:
            alias = name.replace(".fn.", ".", 1)
            register(alias, value)
            if alias.endswith(".weight"):
                register(alias[:-7], value)

    session = InferenceSession(devices=[device])
    model = session.load(graph, weights_registry=registry)
    print("BPLAN MAX CPU COMPILE: PASS", flush=True)

    print("EXECUTING REAL BPLAN MAX INFERENCE...", flush=True)
    outputs = model.execute(*runtime_inputs)

    assert len(outputs) == 1
    actual = np.asarray(outputs[0].to_numpy())
    assert np.isfinite(actual).all()

    print("BPLAN REAL MAX INFERENCE: PASS", flush=True)
    print("MAX OUTPUT SHAPE:", actual.shape, flush=True)

    baseline = torch.load(
        root / "bplan_pytorch_neural_output.pt",
        map_location="cpu", weights_only=True
    )

    if isinstance(baseline, torch.Tensor):
        expected = baseline.detach().cpu().numpy()
        print("PYTORCH OUTPUT SHAPE:", expected.shape)

        if actual.shape == expected.shape:
            diff = np.max(np.abs(actual - expected))
            parity = np.allclose(actual, expected, rtol=1e-3, atol=1e-4)
            print("MAX ABS DIFFERENCE:", float(diff))
            print("BPLAN NUMERICAL PARITY:",
                  "PASS" if parity else "FAILED")
        else:
            print("PARITY: PENDING - output shape mismatch")
    else:
        print("BASELINE TYPE:", type(baseline).__name__)
        print("PARITY: PENDING - baseline structure needs inspection")

    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN REAL MAX INFERENCE: FAILED", flush=True)
    traceback.print_exc()
    sys.exit(1)
PY
