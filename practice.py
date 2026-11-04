
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
ROOT="$PWD"
IMAGE=""

for CID in 87202aa5f06a 225c544812ad 393fc64b1a75 d8578435c7b; do
    IMG=$("${P[@]}" inspect --format '{{.Image}}' "$CID" 2>/dev/null || true)
    if [ -n "$IMG" ] && "${P[@]}" image exists "$IMG"; then
        IMAGE="$IMG"
        break
    fi
done

[ -n "$IMAGE" ] || { echo "BLOCKED: Existing PyTorch image unavailable"; exit 1; }

"${P[@]}" run --rm -i \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,size=2g \
  -e HOME=/tmp \
  -e HF_HOME=/tmp/hf \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$ROOT:$ROOT:ro" \
  -w "$ROOT" \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" - <<'PY'
import sys
import json
import inspect
import traceback
from pathlib import Path

import torch

torch.set_num_threads(2)

root = Path.cwd()
original = root / "artifacts/v1.472"
validation = root / "artifacts/v1.472-max/pzaas_max/validation"

print("=== PZAAS ORIGINAL PYTORCH REPLAY ===", flush=True)

try:
    sys.path.insert(
        0,
        str(original / "utils/dependency-utils")
    )

    from models import GRecBase

    params_files = sorted(
        original.rglob("torch_model_params_base.json")
    )

    if len(params_files) != 1:
        raise RuntimeError(
            f"Expected one base parameter file; found {len(params_files)}"
        )

    with open(params_files[0]) as f:
        raw = json.load(f)

    params = raw[0] if isinstance(raw, list) else raw

    if not isinstance(params, dict):
        raise RuntimeError("Invalid original model parameters")

    # Match the original pipeline's base-model loader.
    params["transfer_ind"] = True
    params["extract_deep_idx"] = -1

    config = params.get("nlp_encoder_path")

    if not config or not Path(config).is_file():
        candidates = []
        for p in original.rglob("config.json"):
            try:
                with open(p) as f:
                    obj = json.load(f)
                if "debert" in str(obj.get("model_type", "")).lower():
                    candidates.append(p)
            except (OSError, ValueError):
                continue

        if len(candidates) != 1:
            raise RuntimeError(
                "Original DeBERT config unresolved: "
                + str([str(p) for p in candidates])
            )

        params["nlp_encoder_path"] = str(candidates[0])

    print("MODEL CONFIG: FOUND", flush=True)

    checkpoint = original / "core-artifact/model_0_base.pt"

    if not checkpoint.is_file():
        raise RuntimeError("Original base checkpoint missing")

    model = GRecBase(**params)

    state = torch.load(
        checkpoint,
        map_location="cpu",
        weights_only=True
    )

    model.load_state_dict(state, strict=True)
    model.eval()

    print("TRAINED BASE MODEL: LOADED", flush=True)

    saved = torch.load(
        validation / "ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )

    inputs = saved["model_in"]

    if not isinstance(inputs, dict):
        raise RuntimeError("Saved model_in is not a dictionary")

    signature = inspect.signature(model.forward)

    kwargs = {}
    missing = []

    for name, parameter in signature.parameters.items():
        if name == "self":
            continue

        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        ):
            continue

        if name in inputs:
            kwargs[name] = inputs[name]
        elif parameter.default is inspect.Parameter.empty:
            missing.append(name)

    if missing:
        raise RuntimeError(
            "Required original inputs missing: " + str(missing)
        )

    print("SAME INPUT: MAPPED", flush=True)

    with torch.inference_mode():
        actual = model(**kwargs)

    if not isinstance(actual, torch.Tensor):
        raise RuntimeError(
            "Original model returned " + str(type(actual))
        )

    reference = torch.load(
        validation / "ppa_model_base_reference.pt",
        map_location="cpu",
        weights_only=True
    )

    if not isinstance(reference, torch.Tensor):
        raise RuntimeError("Reference is not a tensor")

    actual = actual.detach().cpu().float()
    reference = reference.detach().cpu().float()

    print("ORIGINAL OUTPUT SHAPE:", tuple(actual.shape))
    print("REFERENCE SHAPE:", tuple(reference.shape))

    if actual.shape != reference.shape:
        raise RuntimeError("Original/reference shape mismatch")

    if not torch.isfinite(actual).all():
        raise RuntimeError("Original model produced nonfinite values")

    diff = (actual - reference).abs()

    print("MAX ABS DIFF:", diff.max().item())
    print("MEAN ABS DIFF:", diff.mean().item())

    passed = torch.allclose(
        actual,
        reference,
        rtol=1e-3,
        atol=1e-3
    )

    print(
        "ORIGINAL VS SAVED REFERENCE:",
        "PASS" if passed else "FAIL"
    )

    print(
        "NEXT:",
        "COMPARE VERIFIED REFERENCE WITH MAX"
        if passed else
        "RESOLVE PYTORCH REFERENCE PROVENANCE"
    )

except Exception:
    print("ORIGINAL PYTORCH REPLAY: BLOCKED")
    traceback.print_exc(limit=4)
    sys.exit(1)

finally:
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
PY
SH
