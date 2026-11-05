
cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/pzaas_max/validation && \
podman --root /application1/podman/storage \
  --runroot /run/containers/storage run \
  --rm -i --pull=never --network=none \
  --security-opt label=disable \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/artifacts/v1.472-max/pzaas_max/validation:/outputs:rw" \
  -w /workspace \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import os
import sys
import json
import inspect
import traceback
from pathlib import Path

import torch
import numpy as np

root = Path("/workspace")
base = root / "artifacts/v1.472"
cfg = base / "config"
validation = root / "artifacts/v1.472-max/pzaas_max/validation"

print("=== PZAAS ORIGINAL PYTORCH REPLAY ===", flush=True)
print("PYTORCH:", torch.__version__, flush=True)

try:
    original_config = cfg / "config.json"
    mini_config = cfg / "all-MiniLM-L6-v2/config.json"
    param_path = cfg / "torch_model_params_base.json"
    checkpoint = base / "core-artifact/model_0_base.pt"

    for p in [original_config, mini_config, param_path, checkpoint]:
        if not p.is_file():
            raise FileNotFoundError(str(p))

    a = json.loads(original_config.read_text())
    b = json.loads(mini_config.read_text())

    for name, obj in [("ROOT", a), ("MINILM", b)]:
        assert obj.get("model_type") == "bert", name
        assert obj.get("hidden_size") == 384, name
        assert obj.get("num_hidden_layers") == 6, name

    print("ORIGINAL NLP CONFIG: PASS", flush=True)

    params = json.loads(param_path.read_text())
    if isinstance(params, list):
        params = params[0]

    if not isinstance(params, dict):
        raise TypeError("Unexpected original parameter format")

    # Replicate original pipeline.py loadBaseModel behavior.
    params["nlp_encoder_path"] = str(original_config)
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    model_dir = base / "utils/dependency-utils"
    sys.path.insert(0, str(model_dir))

    from models import GRecBase

    torch.set_grad_enabled(False)
    model = GRecBase(**params)
    state = torch.load(
        checkpoint,
        map_location="cpu",
        weights_only=False
    )

    model.load_state_dict(state, strict=True)
    model.eval()

    print("ORIGINAL GRecBase LOAD: PASS", flush=True)
    print("ORIGINAL CHECKPOINT: PASS", flush=True)

    candidates = [
        validation / "ppa_model_input_exact.pt",
        validation / "ppa_pytorch_reference_01.pt"
    ]

    model_in = None
    input_source = None

    for path in candidates:
        if not path.is_file():
            continue

        data = torch.load(
            path,
            map_location="cpu",
            weights_only=False
        )

        if isinstance(data, dict):
            value = data.get("model_in", data)

            if isinstance(value, dict) and "deep_in" in value:
                model_in = value
                input_source = path
                break

    if model_in is None:
        raise RuntimeError("Saved exact model_in unavailable")

    print("SAVED MODEL INPUT: PASS", flush=True)
    print("SOURCE:", input_source.name, flush=True)

    def cpu_value(value):
        if isinstance(value, torch.Tensor):
            return value.detach().cpu()
        if isinstance(value, (list, tuple)):
            return type(value)(cpu_value(v) for v in value)
        if isinstance(value, dict):
            return {k: cpu_value(v) for k, v in value.items()}
        return value

    aliases = {
        "tasks_in": "task_in",
        "task_in": "tasks_in"
    }

    signature = inspect.signature(model.forward)
    kwargs = {}
    missing = []

    for name, parameter in signature.parameters.items():
        if name == "self" or parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        ):
            continue

        key = name
        if key not in model_in:
            key = aliases.get(name, name)

        if key in model_in:
            kwargs[name] = cpu_value(model_in[key])
        elif parameter.default is inspect.Parameter.empty:
            missing.append(name)

    if missing:
        raise RuntimeError(
            "Missing required original forward inputs: "
            + ", ".join(missing)
        )

    print("ORIGINAL FORWARD INPUT MAPPING: PASS", flush=True)

    with torch.inference_mode():
        result = model(**kwargs)

    def collect(value):
        if isinstance(value, torch.Tensor):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from collect(child)

    outputs = [
        tensor.detach().cpu().float()
        for tensor in collect(result)
        if tuple(tensor.shape) == (1, 2048)
    ]

    if len(outputs) != 1:
        raise RuntimeError(
            f"Expected one (1,2048) output; found {len(outputs)}"
        )

    actual = outputs[0]
    assert torch.isfinite(actual).all()

    print("ORIGINAL PYTORCH EXECUTION: PASS", flush=True)
    print("OUTPUT SHAPE:", tuple(actual.shape), flush=True)

    output_path = Path("/outputs/ppa_pytorch_base_replay.pt")

    torch.save(
        {
            "output": actual,
            "input_source": input_source.name,
            "checkpoint": "model_0_base.pt",
            "config": "config/config.json"
        },
        output_path
    )

    print("REPLAY OUTPUT SAVED:", output_path, flush=True)

    ref_path = validation / "ppa_model_base_reference.pt"

    if ref_path.is_file():
        reference = torch.load(
            ref_path,
            map_location="cpu",
            weights_only=False
        )

        if isinstance(reference, torch.Tensor):
            expected = reference.detach().cpu().float()

            if tuple(expected.shape) == tuple(actual.shape):
                diff = (actual - expected).abs()
                print("=== SAVED REFERENCE COMPARISON ===")
                print("MAX ABS DIFF:", float(diff.max()))
                print("MEAN ABS DIFF:", float(diff.mean()))
                print(
                    "NUMERICAL MATCH:",
                    bool(torch.allclose(
                        actual, expected,
                        rtol=1e-3, atol=1e-3
                    ))
                )
                print(
                    "REFERENCE INPUT PROVENANCE: NOT VERIFIED"
                )
            else:
                print("REFERENCE SHAPE: DIFFERENT")
        else:
            print("REFERENCE FORMAT: NOT DIRECT TENSOR")

    print("\n=== FINAL RESULTS ===")
    print("ORIGINAL PYTORCH REPLAY: PASS")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("NEXT: COMPARE SAME-INPUT PYTORCH AND MAX OUTPUTS")

except Exception as exc:
    print("\nORIGINAL PYTORCH REPLAY: BLOCKED")
    print(type(exc).__name__ + ":", exc)
    traceback.print_exc(limit=4)
    sys.exit(1)
PY
