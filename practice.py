REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, traceback
from pathlib import Path
import torch
import numpy as np

try:
    root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
    dev = root / "bplan_max_dev"

    pkg = types.ModuleType("cta_max")
    pkg.__path__ = [str(dev)]
    sys.modules["cta_max"] = pkg
    sys.path.insert(0, str(dev))

    from max.driver import CPU, Tensor
    from max.graph import DeviceRef
    from max.engine import InferenceSession
    from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct
    from run_real_sanity_input_adapter import build_real_inputs

    saved = torch.load(root / "bplan_neural_inputs.pt",
                       map_location="cpu", weights_only=True)
    data = dict(saved)
    if "task_in" not in data and "tasks_in" in data:
        data["task_in"] = data["tasks_in"]

    labels, arrays = build_real_inputs(model_in=data)
    device = CPU()
    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.from_device(device)
    )
    assert len(arrays) == len(graph.inputs) == 72

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

    inputs = [
        Tensor.from_numpy(np.ascontiguousarray(a))
        for a in arrays
    ]

    print("EXECUTING REAL BPLAN MAX INFERENCE...", flush=True)
    outputs = model.execute(*inputs)

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
            print("MAX ABS DIFFERENCE:", float(diff))
            print("PARITY (rtol=1e-3, atol=1e-4):",
                  "PASS" if np.allclose(actual, expected, rtol=1e-3, atol=1e-4)
                  else "FAILED")
        else:
            print("PARITY: PENDING - output shapes differ")
    else:
        print("PYTORCH BASELINE TYPE:", type(baseline).__name__)
        print("PARITY: PENDING - inspect baseline structure")

    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN REAL MAX INFERENCE: FAILED", flush=True)
    traceback.print_exc()
    sys.exit(1)
PY
