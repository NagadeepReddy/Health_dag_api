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

    pkg = types.ModuleType("cta_max")
    pkg.__path__ = [str(dev)]
    sys.modules["cta_max"] = pkg
    sys.path.insert(0, str(dev))

    from max.driver import CPU, Tensor
    from max.dtype import DType
    from max.graph import Graph, TensorType, DeviceRef
    from max.engine import InferenceSession
    from max.nn import Linear
    from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct
    from run_real_sanity_input_adapter import build_real_inputs

    device = CPU()
    device_ref = DeviceRef.from_device(device)

    saved = dict(torch.load(
        root / "bplan_neural_inputs.pt",
        map_location="cpu", weights_only=True
    ))
    if "task_in" not in saved and "tasks_in" in saved:
        saved["task_in"] = saved["tasks_in"]

    labels, arrays = build_real_inputs(model_in=saved)
    graph = build_grecbase_fusion_graph_order_correct(device_ref)

    assert len(labels) == len(arrays) == len(graph.inputs) == 72
    runtime_inputs = []

    for label, arr, inp in zip(labels, arrays, graph.inputs):
        value = np.asarray(arr)
        expected = np.dtype(str(inp.type.dtype).split(".")[-1])
        assert tuple(value.shape) == tuple(int(d) for d in inp.type.shape), label
        if value.dtype != expected:
            assert value.dtype == np.int64 and expected == np.float32, label
            cast = value.astype(np.float32)
            assert np.array_equal(value, cast.astype(np.int64)), label
            value = cast
        runtime_inputs.append(Tensor.from_numpy(np.ascontiguousarray(value)))

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
    base_model = session.load(graph, weights_registry=registry)
    base_output = np.asarray(
        base_model.execute(*runtime_inputs)[0].to_numpy(),
        dtype=np.float32
    )
    assert base_output.shape == (1, 2048)
    assert np.isfinite(base_output).all()
    print("BPLAN MAX BASE INFERENCE: PASS", flush=True)

    transfer = torch.load(
        "artifacts/v1.113/core-artifact/bplan_model.pt",
        map_location="cpu", weights_only=True
    )
    if "state_dict" in transfer:
        transfer = transfer["state_dict"]

    head_weight = transfer["dense1.weight"].detach().cpu().float().numpy()
    assert head_weight.shape == (10438, 2048)

    head_graph = Graph(
        "bplan_full_prediction_head",
        input_types=[TensorType(DType.float32, [1, 2048], device=device_ref)]
    )
    with head_graph:
        head = Linear(
            in_dim=2048, out_dim=10438,
            dtype=DType.float32, device=device_ref,
            has_bias=False, name="bplan_prediction_head"
        )
        head_graph.output(head(head_graph.inputs[0]))

    head_model = session.load(
        head_graph,
        weights_registry={"bplan_prediction_head.weight": head_weight}
    )
    actual = np.asarray(
        head_model.execute(
            Tensor.from_numpy(np.ascontiguousarray(base_output))
        )[0].to_numpy()
    )

    assert actual.shape == (1, 10438)
    assert np.isfinite(actual).all()
    print("BPLAN FULL MAX INFERENCE: PASS", flush=True)

    baseline = torch.load(
        root / "bplan_pytorch_neural_output.pt",
        map_location="cpu", weights_only=True
    )
    assert isinstance(baseline, torch.Tensor)
    expected = baseline.detach().cpu().numpy()
    assert expected.shape == actual.shape, (actual.shape, expected.shape)

    diff = float(np.max(np.abs(actual - expected)))
    parity = bool(np.allclose(actual, expected, rtol=1e-3, atol=1e-4))

    print("FULL OUTPUT SHAPE:", actual.shape)
    print("MAX ABS DIFFERENCE:", diff)
    print("BPLAN FULL NUMERICAL PARITY:", "PASS" if parity else "FAILED")
    print("ORIGINAL DS AND CTA: UNCHANGED")
    if not parity:
        sys.exit(2)

except Exception:
    print("BPLAN FULL MAX VALIDATION: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
