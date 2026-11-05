cd /application1/sajjna8/rt-pzaas-v1.0 && podman --root /application1/podman/storage --runroot /run/containers/storage run --rm -i --pull=never --network=none --security-opt label=disable -v "$PWD:/workspace:ro" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, json, inspect, traceback
from pathlib import Path
import numpy as np
import torch

print("=== PZAAS DIRECT LAYER-0 MAX PARITY ===", flush=True)

root = Path("/workspace/artifacts/v1.472")
maxroot = Path("/workspace/artifacts/v1.472-max")
val = maxroot / "pzaas_max/validation"

sys.path.insert(0, str(root / "utils/dependency-utils"))
sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(maxroot))

torch.set_num_threads(2)

try:
    from models import GRecBase

    params = json.loads(
        (root / "config/torch_model_params_base.json").read_text()
    )
    if isinstance(params, list):
        params = params[0]

    params["nlp_encoder_path"] = str(root / "config/config.json")
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    model = GRecBase(**params)
    state = torch.load(
        root / "core-artifact/model_0_base.pt",
        map_location="cpu",
        weights_only=False
    )
    model.load_state_dict(state, strict=True)
    model.eval()
    print("ORIGINAL MODEL: PASS", flush=True)

    saved = torch.load(
        val / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=False
    )
    data = saved.get("model_in", saved)

    modules = dict(model.named_modules())
    prefix = "sequence_transformer.ptransformer.0"

    required = [
        prefix,
        prefix + ".fn",
        prefix + ".fn.rotary_emb"
    ]

    for name in required:
        if name not in modules:
            raise RuntimeError("Original module missing: " + name)

    captured = {}
    handles = []

    def save_tensor(key, value):
        if isinstance(value, (tuple, list)):
            value = next(
                (v for v in value if isinstance(v, torch.Tensor)),
                None
            )
        if not isinstance(value, torch.Tensor):
            raise RuntimeError("Non-tensor stage: " + key)
        captured[key] = value.detach().cpu().numpy().copy()

    handles.append(
        modules[prefix + ".fn"].register_forward_pre_hook(
            lambda m, args: save_tensor("x", args[0])
        )
    )
    handles.append(
        modules[prefix + ".fn.rotary_emb"].register_forward_hook(
            lambda m, args, output: save_tensor("pos", output)
        )
    )
    handles.append(
        modules[prefix + ".fn"].register_forward_hook(
            lambda m, args, output: save_tensor("fn", output)
        )
    )
    handles.append(
        modules[prefix].register_forward_hook(
            lambda m, args, output: save_tensor("residual", output)
        )
    )

    sig = inspect.signature(model.forward)
    arguments = {}
    aliases = {"tasks_in": "task_in", "task_in": "tasks_in"}

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name in data:
            arguments[name] = data[name]
        elif aliases.get(name) in data:
            arguments[name] = data[aliases[name]]
        elif param.default is inspect.Parameter.empty:
            raise RuntimeError("Missing input: " + name)

    try:
        with torch.inference_mode():
            model(**arguments)
    finally:
        for h in handles:
            h.remove()

    assert set(captured) == {"x", "pos", "fn", "residual"}

    x = np.ascontiguousarray(captured["x"], dtype=np.float32)
    pos = np.asarray(captured["pos"], dtype=np.float32)
    expected = np.asarray(captured["fn"], dtype=np.float32)
    residual = np.asarray(captured["residual"], dtype=np.float32)

    if pos.shape == (50, 256):
        pos = pos.reshape(1, 1, 50, 256)

    pos = np.ascontiguousarray(pos, dtype=np.float32)
    valid = np.ascontiguousarray(
        np.asarray(data["v1_in"], dtype=np.int64).reshape(1)
    )

    assert x.shape == (1, 50, 256)
    assert pos.shape == (1, 1, 50, 256)
    assert expected.shape == x.shape
    assert residual.shape == x.shape

    print("PYTORCH DIRECT CAPTURE: PASS", flush=True)
    print("LAYER INPUT:", x.shape)
    print("ROTARY:", pos.shape)
    print("VALID LENGTH:", valid.tolist())

    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, TensorType, DeviceRef
    from pzaas_max.parallel_transformer_block_2layers import (
        ParallelTransformerBlockMAX
    )

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_exact_layer0",
        input_types=[
            TensorType(DType.float32, [1, 50, 256], device=device),
            TensorType(DType.float32, [1, 1, 50, 256], device=device),
            TensorType(DType.int64, [1], device=device)
        ]
    ) as graph:
        gx, gp, gv = [v.tensor for v in graph.inputs]
        block = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )
        graph.output(block(gx, gp, gv))

    print("MAX ISOLATED GRAPH: PASS", flush=True)

    registry = {}
    for key, value in state.items():
        if isinstance(value, torch.Tensor):
            registry[key] = np.ascontiguousarray(
                value.detach().cpu().numpy(),
                dtype=np.float32
            )

    session = InferenceSession(devices=[CPU()])
    compiled = session.load(graph, weights_registry=registry)
    print("MAX CPU COMPILATION: PASS", flush=True)

    actual = compiled.execute(x, pos, valid)[0].to_numpy()
    actual = np.asarray(actual, dtype=np.float32)

    assert actual.shape == expected.shape

    diff = np.abs(actual - expected)
    residual_diff = np.abs((x + actual) - residual)

    ok = np.allclose(actual, expected, rtol=1e-3, atol=1e-3)
    residual_ok = np.allclose(
        x + actual, residual, rtol=1e-3, atol=1e-3
    )

    print("\n=== NUMERICAL RESULTS ===")
    print("FN MAX DIFF:", float(diff.max()))
    print("FN MEAN DIFF:", float(diff.mean()))
    print("FN PARITY:", "PASS" if ok else "FAIL")
    print("RESIDUAL MAX DIFF:", float(residual_diff.max()))
    print("RESIDUAL PARITY:", "PASS" if residual_ok else "FAIL")

    print("\n=== NEXT ===")
    if ok and residual_ok:
        print("LAYER 0: PASS")
        print("NEXT: VERIFY FEATURE ASSEMBLY AND LAYER 1")
    else:
        print("LAYER 0: DIVERGENCE CONFIRMED")
        print("NEXT: CORRECT FIRST DIFFERENT RMSNORM/QKV/ROTARY/MASK")

except Exception as exc:
    print("\nDIAGNOSTIC: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=5)
    raise SystemExit(1)

finally:
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("FILES MODIFIED: NONE")
PY
