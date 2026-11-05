cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run \
--rm -i --pull=never --network=none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, json, traceback
from pathlib import Path
import numpy as np
import torch

print("=== PZAAS EXACT TRANSFORMER LAYER-0 PARITY ===", flush=True)

root = Path("/workspace/artifacts/v1.472")
mx = Path("/workspace/artifacts/v1.472-max")
val = mx / "pzaas_max/validation"

sys.path.insert(0, str(root / "utils/dependency-utils"))
sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(mx))

torch.set_num_threads(2)

try:
    from models import GRecBase

    config = json.loads(
        (root / "config/torch_model_params_base.json").read_text()
    )
    if isinstance(config, list):
        config = config[0]

    config["nlp_encoder_path"] = str(root / "config/config.json")
    config["transfer_ind"] = True
    config["extract_deep_idx"] = -1

    model = GRecBase(**config)

    state = torch.load(
        root / "core-artifact/model_0_base.pt",
        map_location="cpu",
        weights_only=False
    )

    model.load_state_dict(state, strict=True)
    model.eval()
    print("ORIGINAL PYTORCH MODEL: PASS", flush=True)

    saved = torch.load(
        val / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=False
    )
    data = saved.get("model_in", saved)

    stages = np.load(
        val / "ppa_pytorch_sequence_stages.npz"
    )

    print("SAVED PYTORCH STAGES:", len(stages.files))

    captured = {}

    candidates = [
        (n, m) for n, m in model.named_modules()
        if "sequence_transformer" in n and n.endswith(".0.fn")
    ]

    if len(candidates) != 1:
        raise RuntimeError(
            "Expected one first transformer module; found "
            + str([n for n, _ in candidates])
        )

    name, module = candidates[0]

    def capture_input(mod, inputs):
        captured["x"] = (
            inputs[0].detach().cpu().float().numpy().copy()
        )

    handle = module.register_forward_pre_hook(capture_input)

    try:
        import inspect
        signature = inspect.signature(model.forward)
        args = {}
        aliases = {"tasks_in": "task_in", "task_in": "tasks_in"}

        for key, parameter in signature.parameters.items():
            if key == "self":
                continue
            if key in data:
                args[key] = data[key]
            elif aliases.get(key) in data:
                args[key] = data[aliases[key]]
            elif parameter.default is inspect.Parameter.empty:
                raise RuntimeError("Missing required input: " + key)

        with torch.inference_mode():
            model(**args)
    finally:
        handle.remove()

    x = np.ascontiguousarray(captured["x"], dtype=np.float32)

    fn_keys = [
        k for k in stages.files if k.endswith("__0__fn")
    ]
    pos_keys = [
        k for k in stages.files
        if "__0__fn__rotary_emb" in k
    ]
    residual_keys = [
        k for k in stages.files if k.endswith("__0")
    ]

    if not (len(fn_keys) == len(pos_keys) == len(residual_keys) == 1):
        raise RuntimeError(
            "Saved transformer stage identification is ambiguous"
        )

    expected_fn = np.asarray(stages[fn_keys[0]], dtype=np.float32)
    expected_residual = np.asarray(
        stages[residual_keys[0]], dtype=np.float32
    )
    position = np.asarray(stages[pos_keys[0]], dtype=np.float32)

    if position.shape == (50, 256):
        position = position[None, None, :, :]

    position = np.ascontiguousarray(position, dtype=np.float32)
    valid = np.ascontiguousarray(
        np.asarray(data["v1_in"], dtype=np.int64).reshape(1)
    )

    assert x.shape == (1, 50, 256), x.shape
    assert position.shape == (1, 1, 50, 256), position.shape
    assert expected_fn.shape == x.shape
    assert expected_residual.shape == x.shape

    print("EXACT FIRST-LAYER INPUT:", x.shape)
    print("ROTARY INPUT:", position.shape)
    print("VALID LENGTH:", valid.tolist())
    print("PYTORCH PRE-HOOK: PASS", flush=True)

    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import DeviceRef, Graph, TensorType

    from pzaas_max.parallel_transformer_block_2layers import (
        ParallelTransformerBlockMAX
    )

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_layer0_isolated_parity",
        input_types=[
            TensorType(DType.float32, [1, 50, 256], device=device),
            TensorType(DType.float32, [1, 1, 50, 256], device=device),
            TensorType(DType.int64, [1], device=device),
        ]
    ) as graph:

        gx, gp, gv = [
            v.tensor for v in graph.inputs
        ]

        block = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )

        result = block(gx, gp, gv)
        graph.output(result)

    print("ISOLATED MAX LAYER-0 GRAPH: PASS", flush=True)

    registry = {}

    for key, tensor in state.items():
        if not isinstance(tensor, torch.Tensor):
            continue

        if not key.startswith("sequence_transformer."):
            continue

        array = np.array(
            tensor.detach().cpu().numpy(),
            dtype=np.float32,
            copy=True,
            order="C"
        )

        registry[key] = array

        if ".fn." in key:
            registry[key.replace(".fn.", ".")] = array

    session = InferenceSession(devices=[CPU()])

    compiled = session.load(
        graph,
        weights_registry=registry
    )

    print("MAX LAYER-0 CPU COMPILATION: PASS", flush=True)

    actual_fn = compiled.execute(
        x, position, valid
    )[0].to_numpy()

    actual_fn = np.asarray(actual_fn, dtype=np.float32)

    if actual_fn.shape != expected_fn.shape:
        raise RuntimeError(
            f"Output shape mismatch: {actual_fn.shape} "
            f"vs {expected_fn.shape}"
        )

    diff_fn = np.abs(actual_fn - expected_fn)
    actual_residual = x + actual_fn
    diff_residual = np.abs(actual_residual - expected_residual)

    fn_ok = bool(np.allclose(
        actual_fn, expected_fn, rtol=1e-3, atol=1e-3
    ))
    residual_ok = bool(np.allclose(
        actual_residual, expected_residual,
        rtol=1e-3, atol=1e-3
    ))

    print("\n=== FIRST TRANSFORMER COMPARISON ===")
    print("PYTORCH FN SHAPE:", expected_fn.shape)
    print("MAX FN SHAPE:", actual_fn.shape)
    print("FN MAX ABS DIFF:", float(diff_fn.max()))
    print("FN MEAN ABS DIFF:", float(diff_fn.mean()))
    print("FN PARITY:", "PASS" if fn_ok else "FAIL")
    print("RESIDUAL MAX DIFF:", float(diff_residual.max()))
    print("RESIDUAL PARITY:", "PASS" if residual_ok else "FAIL")

    print("\n=== NEXT DECISION ===")
    if fn_ok and residual_ok:
        print("LAYER 0: PASS")
        print("NEXT: CHECK PRE-TRANSFORMER FEATURE ASSEMBLY")
    else:
        print("LAYER 0: NUMERICAL DIVERGENCE CONFIRMED")
        print("NEXT: ISOLATE RMSNORM / QKV / ROTARY / MASK")

    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("FILES MODIFIED: NONE")

except Exception as exc:
    print("\nLAYER-0 DIAGNOSTIC: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=5)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    raise SystemExit(1)
PY
