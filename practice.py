cd /application1/sajjna8/rt-pzaas-v1.0 && podman --root /application1/podman/storage --runroot /run/containers/storage run --rm -i --pull=never --network=none --security-opt label=disable -v "$PWD:/workspace:ro" -w /workspace --entrypoint python localhost/cta-max-faiss:local - <<'PY'
import sys, json, inspect, re, traceback
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.472")
mx = Path("/workspace/artifacts/v1.472-max")
val = mx / "pzaas_max/validation"

sys.path[:0] = [
    str(root / "utils/dependency-utils"),
    str(root / "core-artifact"),
    str(mx)
]
torch.set_num_threads(2)

print("=== PZAAS SAME-INPUT FULL PARITY ===", flush=True)

try:
    from models import GRecBase
    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, TensorType, DeviceRef

    from pzaas_max.grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )
    from pzaas_max.parallel_transformer_block_2layers import (
        ParallelTransformerBlockMAX
    )

    params = json.loads(
        (root / "config/torch_model_params_base.json").read_text()
    )
    if isinstance(params, list):
        params = params[0]

    params["nlp_encoder_path"] = str(root / "config/config.json")
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    state = torch.load(
        root / "core-artifact/model_0_base.pt",
        map_location="cpu",
        weights_only=False
    )
    if "state_dict" in state:
        state = state["state_dict"]

    model = GRecBase(**params)
    model.load_state_dict(state, strict=True)
    model.eval()

    saved = torch.load(
        val / "ppa_model_input_exact.pt",
        map_location="cpu",
        weights_only=False
    )
    data = saved.get("model_in", saved)

    # CRITICAL: lowercase L, NOT digit 1.
    assert "vl_in" in data
    assert "sibling_vl_in" in data

    print("ORIGINAL MODEL: PASS")
    print("CORRECT INPUT NAMES: PASS")

    modules = dict(model.named_modules())
    layer = modules["sequence_transformer.ptransformer.0"]
    fn = layer.fn

    captured = {}
    handles = []

    handles.append(
        fn.register_forward_pre_hook(
            lambda m, args: captured.update(
                x=args[0].detach().cpu().clone()
            )
        )
    )
    handles.append(
        fn.register_forward_hook(
            lambda m, args, out: captured.update(
                fn=out.detach().cpu().clone()
            )
        )
    )
    handles.append(
        layer.register_forward_hook(
            lambda m, args, out: captured.update(
                residual=out.detach().cpu().clone()
            )
        )
    )

    aliases = {
        "tasks_in": "task_in",
        "task_in": "tasks_in"
    }
    kwargs = {}

    for name, p in inspect.signature(model.forward).parameters.items():
        if name == "self":
            continue
        key = name if name in data else aliases.get(name)
        if key in data:
            kwargs[name] = data[key]
        elif p.default is inspect.Parameter.empty:
            raise KeyError("Missing original input: " + name)

    try:
        with torch.inference_mode():
            original = model(**kwargs)
    finally:
        for h in handles:
            h.remove()

    if isinstance(original, (tuple, list)):
        original = next(
            (
                x for x in original
                if isinstance(x, torch.Tensor)
                and tuple(x.shape) == (1, 2048)
            ),
            None
        )

    if not isinstance(original, torch.Tensor):
        raise RuntimeError("Original output is not a (1,2048) tensor")

    expected = original.detach().cpu().numpy().astype(np.float32)

    reference = torch.load(
        val / "ppa_model_base_reference.pt",
        map_location="cpu",
        weights_only=False
    )
    if isinstance(reference, dict):
        reference = reference["output"]
    if isinstance(reference, torch.Tensor):
        reference = reference.detach().cpu().numpy()
    reference = np.asarray(reference, dtype=np.float32).reshape(1,2048)

    assert np.allclose(
        expected, reference, rtol=1e-3, atol=1e-3
    ), "Original replay does not match saved reference"

    print("ORIGINAL PYTORCH REPLAY: PASS")
    print("SAME-INPUT REFERENCE: PASS")

    def arr(x, dtype=None):
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        return np.ascontiguousarray(np.asarray(x, dtype=dtype))

    def scalar(x):
        return arr(x, np.int64).reshape(1)

    tasks = data["task_in"]
    deep = data["deep_in"]
    wide = data["wide_in"]

    sd = arr(data["sibling_deep_in"], np.int64)
    sw = arr(data["sibling_wide_in"], np.float32)

    assert len(tasks) == 2
    assert len(deep) == 17
    assert len(wide) == 127
    assert sd.shape == (1,3,10)
    assert sw.shape == (1,18,10)

    x = arr(captured["x"], np.float32)
    fn_expected = arr(captured["fn"], np.float32)
    residual_expected = arr(captured["residual"], np.float32)

    rotary = fn.get_rotary_embedding(
        x.shape[1], torch.device("cpu")
    )
    rotary = arr(rotary, np.float32)
    assert rotary.shape == (50,256)
    rotary = rotary.reshape(1,1,50,256)

    page_wide = data["page_meta_wide_in"]
    assert len(page_wide) == 1

    packed = [
        scalar(tasks[0]),
        scalar(tasks[1]),
        arr(data["ihq_in"], np.int64),
        arr(data["jet_name_in"], np.int64),
        arr(data["jet_status_in"], np.int64)
    ]

    packed += [scalar(v) for v in deep]

    packed.append(
        np.asarray(
            [arr(v).reshape(-1)[0] for v in wide],
            dtype=np.float32
        ).reshape(1,127)
    )

    packed += [
        arr(data["input_ids"], np.int64),
        arr(data["attention_mask"], np.int64),
        arr(data["page_in"], np.int64),
        arr(data["item_in"], np.int64),
        arr(data["item_meta_in"], np.int64),
        arr(page_wide[0], np.float32).reshape(1,50,1),
        rotary
    ]

    for i in range(10):
        for j in range(3):
            packed.append(
                arr(sd[:,j,i], np.int64).reshape(1)
            )
        packed.append(
            arr(sw[:,:,i], np.float32).reshape(1,18)
        )

    packed += [
        scalar(data["vl_in"]),
        scalar(data["sibling_vl_in"])
    ]

    assert len(packed) == 72

    print("EXACT 72-INPUT PACKING: PASS")

    device = DeviceRef.CPU()
    graph = build_grecbase_fusion_graph_order_correct(device)
    assert len(graph.inputs) == 72

    print("MAX GRAPH: PASS")

    def find_weight(name):
        candidates = [name]

        if not name.endswith(".weight"):
            candidates.append(name + ".weight")

        with_fn = re.sub(
            r"(\.ptransformer\.\d+\.)(?!fn\.)",
            r"\1fn.",
            name
        )

        if with_fn != name:
            candidates.extend([
                with_fn,
                with_fn + ".weight"
            ])

        for candidate in candidates:
            if candidate in state:
                return candidate

        raise KeyError("Unresolved trained weight: " + name)

    registry = {}

    for w in graph.weights:
        name = w.name
        registry[name] = arr(
            state[find_weight(name)], np.float32
        )

    assert len(registry) == 17
    print("TRAINED GRAPH WEIGHTS: 17/17 PASS")

    session = InferenceSession(devices=[CPU()])
    compiled = session.load(
        graph,
        weights_registry=registry
    )

    print("MAX CPU COMPILATION: PASS", flush=True)

    actual = arr(
        compiled.execute(*packed)[0].to_numpy(),
        np.float32
    )
    assert actual.shape == (1,2048)

    print("MAX CPU EXECUTION: PASS")

    print("\n=== EIGHT-BRANCH PARITY ===")

    branches = [
        "sequence", "context", "search0", "search1",
        "jet", "ihq", "sibling", "task"
    ]
    passed = []

    for i, name in enumerate(branches):
        s = slice(i*256, (i+1)*256)
        a = actual[:,s]
        e = expected[:,s]

        diff = np.abs(a-e)
        ok = np.allclose(a,e,rtol=1e-3,atol=1e-3)
        passed.append(ok)

        print(
            f"{name}: {'PASS' if ok else 'FAIL'} "
            f"| max={diff.max():.8g} "
            f"| mean={diff.mean():.8g}"
        )

    all_branches = all(passed)
    full_diff = np.abs(actual-expected)
    full_ok = np.allclose(
        actual,expected,rtol=1e-3,atol=1e-3
    )

    print("\n=== FULL MODEL PARITY ===")
    print("MAX OUTPUT:", actual.shape)
    print("PYTORCH OUTPUT:", expected.shape)
    print("MAX ABS DIFF:",float(full_diff.max()))
    print("MEAN ABS DIFF:",float(full_diff.mean()))
    print("FULL MODEL:", "PASS" if full_ok else "FAIL")

    print("\n=== DIRECT LAYER-0 PARITY ===")

    with Graph(
        "pzaas_layer0_direct",
        input_types=[
            TensorType(
                DType.float32,list(x.shape),device=device
            ),
            TensorType(
                DType.float32,list(rotary.shape),device=device
            ),
            TensorType(
                DType.int64,[1],device=device
            )
        ]
    ) as lg:
        gx,gp,gv = [v.tensor for v in lg.inputs]

        block = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )
        lg.output(block(gx,gp,gv))

    layer_weights = {
        w.name: arr(
            state[find_weight(w.name)],np.float32
        )
        for w in lg.weights
    }

    lcompiled = session.load(
        lg,
        weights_registry=layer_weights
    )

    layer_actual = arr(
        lcompiled.execute(
            x,rotary,scalar(data["vl_in"])
        )[0].to_numpy(),
        np.float32
    )

    assert layer_actual.shape == fn_expected.shape

    layer_diff = np.abs(layer_actual-fn_expected)

    layer_ok = np.allclose(
        layer_actual,fn_expected,rtol=1e-3,atol=1e-3
    )

    residual_diff = np.abs(
        x+layer_actual-residual_expected
    )

    residual_ok = np.allclose(
        x+layer_actual,
        residual_expected,
        rtol=1e-3,
        atol=1e-3
    )

    print("LAYER-0 FN:", "PASS" if layer_ok else "FAIL")
    print("LAYER-0 MAX DIFF:",float(layer_diff.max()))
    print(
        "LAYER-0 RESIDUAL:",
        "PASS" if residual_ok else "FAIL"
    )
    print(
        "RESIDUAL MAX DIFF:",
        float(residual_diff.max())
    )

    print("\n=== FINAL STATUS ===")
    print("LAYER-0:", "PASS" if layer_ok and residual_ok else "FAIL")
    print("EIGHT BRANCHES:",sum(passed),"/8")
    print("FULL MODEL:", "PASS" if full_ok else "FAIL")

    if not (
        layer_ok and residual_ok
        and all_branches and full_ok
    ):
        print("NUMERICAL PARITY: NOT YET ESTABLISHED")
        print("NEXT: CORRECT THE IDENTIFIED MAX DIVERGENCE")
        raise SystemExit(2)

    print("PZAAS ALL NUMERICAL PARITY: PASS")

except Exception as exc:
    print("VALIDATION BLOCKED:",type(exc).__name__,str(exc))
    traceback.print_exc(limit=5)
    raise SystemExit(1)

finally:
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("SOURCE MODIFICATIONS: NONE")
PY
