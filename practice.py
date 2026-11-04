cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import sys, json, inspect, hashlib, traceback
from pathlib import Path
import torch

torch.set_num_threads(2)

root = Path.cwd()
art = root / "artifacts/v1.472"
val = root / "artifacts/v1.472-max/pzaas_max/validation"

print("=== PZAAS ORIGINAL PYTORCH SAME-INPUT REPLAY ===", flush=True)

try:
    checkpoint = art / "core-artifact/model_0_base.pt"
    models_dir = art / "utils/dependency-utils"
    config_files = list(art.rglob("torch_model_params_base.json"))

    assert checkpoint.is_file(), "Original base checkpoint missing"
    assert (models_dir / "models.py").is_file(), "Original models.py missing"
    assert len(config_files) == 1, (
        f"Expected one original base config, found: {config_files}"
    )

    source = None
    model_in = None

    for name in (
        "ppa_pytorch_reference_01.pt",
        "ppa_model_input_exact.pt"
    ):
        p = val / name
        if not p.is_file():
            continue

        obj = torch.load(p, map_location="cpu", weights_only=False)

        if isinstance(obj, dict) and isinstance(obj.get("model_in"), dict):
            source = p
            model_in = obj["model_in"]
            break

        if isinstance(obj, dict) and "deep_in" in obj:
            source = p
            model_in = obj
            break

    assert model_in is not None, "Exact original model_in not found"

    print("SAVED INPUT:", source.name, flush=True)

    with config_files[0].open() as f:
        payload = json.load(f)

    params = payload[0] if isinstance(payload, list) else payload
    assert isinstance(params, dict), "Unexpected original config structure"

    params = dict(params)
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    original_nlp = params.get("nlp_encoder_path")
    candidates = []

    if original_nlp:
        candidate = Path(original_nlp)
        candidates.extend([
            candidate,
            root / candidate,
            config_files[0].parent / candidate
        ])

    selected = next(
        (p for p in candidates if p.is_file()),
        None
    )

    if selected is None:
        matches = [
            p for p in art.rglob("config.json")
            if "debert" in str(p).lower()
        ]
        if len(matches) == 1:
            selected = matches[0]

    assert selected is not None, (
        "Original NLP encoder config unresolved; "
        f"configured={original_nlp}"
    )

    params["nlp_encoder_path"] = str(selected.resolve())

    sys.path.insert(0, str(models_dir.resolve()))
    from models import GRecBase

    print("ORIGINAL MODEL: GRecBase", flush=True)

    model = GRecBase(**params)
    state = torch.load(
        checkpoint, map_location="cpu", weights_only=False
    )
    model.load_state_dict(state, strict=True)
    model.eval()

    print("ORIGINAL CHECKPOINT: STRICT LOAD PASS", flush=True)

    aliases = {
        "tasks_in": "task_in",
        "task_in": "task_in",
        "vl_in": "vl_in",
        "sibling_vl_in": "sibling_vl_in",
    }

    signature = inspect.signature(model.forward)
    kwargs = {}

    for name, parameter in signature.parameters.items():
        if name == "self":
            continue

        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        ):
            continue

        key = aliases.get(name, name)

        if key in model_in:
            kwargs[name] = model_in[key]
        elif parameter.default is inspect.Parameter.empty:
            raise RuntimeError(
                f"Required original forward input missing: {name}"
            )

    def cpu_value(x):
        if isinstance(x, torch.Tensor):
            return x.detach().cpu()
        if isinstance(x, (list, tuple)):
            return type(x)(cpu_value(v) for v in x)
        if isinstance(x, dict):
            return {k: cpu_value(v) for k, v in x.items()}
        return x

    kwargs = {k: cpu_value(v) for k, v in kwargs.items()}

    print("FORWARD ARGUMENTS:", list(kwargs), flush=True)
    print("EXECUTING ORIGINAL PYTORCH...", flush=True)

    with torch.inference_mode():
        result = model(**kwargs)

    def tensors(value):
        if isinstance(value, torch.Tensor):
            return [value.detach().cpu()]
        if isinstance(value, (list, tuple)):
            return [t for v in value for t in tensors(v)]
        if isinstance(value, dict):
            return [t for v in value.values() for t in tensors(v)]
        return []

    outputs = tensors(result)
    assert outputs, "Original model returned no tensors"

    print("PYTORCH INFERENCE: PASS", flush=True)

    for i, tensor in enumerate(outputs):
        print(
            f"OUTPUT {i}: shape={tuple(tensor.shape)} "
            f"dtype={tensor.dtype}",
            flush=True
        )

    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()

    destination = val / "ppa_pytorch_same_input_fresh.pt"

    torch.save({
        "output": cpu_value(result),
        "model_in": model_in,
        "source_file": source.name,
        "source_sha256": fingerprint,
        "checkpoint": str(checkpoint.relative_to(root)),
        "strict_checkpoint_load": True,
        "model_class": "GRecBase"
    }, destination)

    print("\n=== FINAL RESULTS ===")
    print("ORIGINAL PYTORCH EXECUTION: PASS")
    print("SAME-INPUT REFERENCE: SAVED")
    print("REFERENCE FILE:", destination)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("NEXT: COMPARE THIS REFERENCE WITH REAL MAX OUTPUT")

except Exception as exc:
    print("\n=== REPLAY BLOCKED ===")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    raise SystemExit(1)
PY
