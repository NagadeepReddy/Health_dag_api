podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import sys
import json
import numpy as np
import torch
import inspect

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

config = root / "config/torch_model_params_base.json"
nlp_config = root / "config/config.json"
checkpoint = root / "core-artifact/model_0_base.pt"
input_file = base / "real_sanity_model_in.pt"
output_file = base / "real_sanity_pytorch_same_input_verified.npz"

for p in (config, nlp_config, checkpoint, input_file):
    if not p.is_file():
        raise SystemExit(f"STOP: Required existing file missing: {p}")

params = json.loads(config.read_text())
if isinstance(params, list):
    if len(params) != 1:
        raise SystemExit("STOP: Unexpected model config structure")
    params = params[0]

params["nlp_encoder_path"] = str(nlp_config)
params["transfer_ind"] = True
params["extract_deep_idx"] = -1

sys.path.insert(0, str(root / "utils/dependency-utils"))
from models import GRecBase

model = GRecBase(**params)

weights = torch.load(
    checkpoint, map_location="cpu", weights_only=True
)
if isinstance(weights, dict) and "state_dict" in weights:
    weights = weights["state_dict"]

model.load_state_dict(weights, strict=True)
model.eval()

saved = torch.load(
    input_file, map_location="cpu", weights_only=True
)

seq_outputs = []
sibling_outputs = []

def capture_seq(module, args, result):
    seq_outputs.append(result.detach().cpu())

def capture_sibling(module, args, result):
    sibling_outputs.append(result.detach().cpu())

# Hook only modules verified to exist.
if not hasattr(model, "seq_dense"):
    raise SystemExit("STOP: Original sequence module unavailable")
if not hasattr(model, "sibling_context_head"):
    raise SystemExit("STOP: Original sibling module unavailable")

hooks = [
    model.seq_dense.register_forward_hook(capture_seq),
    model.sibling_context_head.register_forward_hook(capture_sibling)
]

signature = inspect.signature(model.forward)
kwargs = {}

for name, parameter in signature.parameters.items():
    key = "task_in" if name == "tasks_in" else name
    if key in saved:
        kwargs[name] = saved[key]
    elif parameter.default is inspect.Parameter.empty:
        raise SystemExit(f"STOP: Missing original input: {name}")

try:
    with torch.inference_mode():
        result = model(**kwargs)
finally:
    for hook in hooks:
        hook.remove()

if not torch.is_tensor(result):
    raise SystemExit("STOP: Unexpected model output type")
if len(seq_outputs) != 1:
    raise SystemExit(
        f"STOP: Expected one sequence output, got {len(seq_outputs)}"
    )
if len(sibling_outputs) != 10:
    raise SystemExit(
        f"STOP: Expected ten sibling outputs, got {len(sibling_outputs)}"
    )

with torch.no_grad():
    stacked = torch.stack(sibling_outputs, dim=1)

    # Original MeanMaxPooling(axis=1) calculation.
    sibling = torch.cat(
        [
            stacked.mean(dim=1),
            stacked.max(dim=1).values
        ],
        dim=-1
    )

references = {
    "sequence": seq_outputs[0].numpy().astype(np.float32),
    "sibling": sibling.numpy().astype(np.float32),
    "final": result.detach().cpu().numpy().astype(np.float32)
}

print("=== ORIGINAL PYTORCH / SAME REAL INPUTS ===")

for name, value in references.items():
    print(
        name,
        "SHAPE:", value.shape,
        "FINITE:", bool(np.isfinite(value).all())
    )
    if not np.isfinite(value).all():
        raise SystemExit("STOP: Nonfinite reference")

if references["final"].shape != (1, 2048):
    raise SystemExit(
        f"STOP: Unexpected final shape {references['final'].shape}"
    )

if output_file.exists():
    with np.load(output_file, allow_pickle=False) as previous:
        same = (
            set(previous.files) == set(references)
            and all(
                np.array_equal(previous[k], references[k])
                for k in references
            )
        )
    if not same:
        raise SystemExit(
            "STOP: Existing verified reference differs; not overwriting"
        )
    print("VERIFIED REFERENCE ALREADY EXISTS AND MATCHES")
else:
    np.savez(output_file, **references)
    print("VERIFIED REFERENCE SAVED:", output_file)

print("ORIGINAL PYTORCH, DS, MAX AND WEIGHTS UNCHANGED")
PY
