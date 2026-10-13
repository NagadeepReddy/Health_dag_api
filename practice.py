podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import sys, json, inspect
import numpy as np
import torch

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

param_files = list(root.rglob("torch_model_params_base.json"))
if len(param_files) != 1:
    raise SystemExit(
        f"STOP: Expected one original base-model config, found: {param_files}"
    )

params = json.loads(param_files[0].read_text())
if isinstance(params, list):
    params = params[0]
if not isinstance(params, dict):
    raise SystemExit("STOP: Unexpected original model config format")

# Preserve the exact original pipeline settings.
params["transfer_ind"] = True
params["extract_deep_idx"] = -1

encoder = Path(str(params.get("nlp_encoder_path", "")))
if not encoder.is_file():
    configs = []
    for p in root.rglob("config.json"):
        try:
            cfg = json.loads(p.read_text())
            if "hidden_size" in cfg and "num_hidden_layers" in cfg:
                configs.append(p)
        except (ValueError, OSError):
            pass

    if len(configs) != 1:
        raise SystemExit(
            f"STOP: Original NLP encoder config not uniquely resolved: {configs}"
        )
    encoder = configs[0]

params["nlp_encoder_path"] = str(encoder)

sys.path.insert(
    0, str(root / "utils" / "dependency-utils")
)

try:
    from models import GRecBase
except ImportError as exc:
    raise SystemExit(
        f"STOP: Original PyTorch model dependency unavailable: {exc}"
    )

checkpoint = torch.load(
    root / "core-artifact" / "model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
if "state_dict" in checkpoint:
    checkpoint = checkpoint["state_dict"]

print("ORIGINAL CONFIG:", param_files[0])
print("ORIGINAL NLP CONFIG:", encoder)

model = GRecBase(**params)
model.load_state_dict(checkpoint, strict=True)
model.eval()

saved = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

signature = inspect.signature(model.forward)
aliases = {"tasks_in": "task_in"}
kwargs = {}

for name, parameter in signature.parameters.items():
    key = aliases.get(name, name)
    if key in saved:
        kwargs[name] = saved[key]
    elif parameter.default is inspect.Parameter.empty:
        raise SystemExit(
            f"STOP: Required original forward input missing: {name}"
        )

sequence_outputs = []
sibling_outputs = []

def capture_sequence(module, inputs, output):
    sequence_outputs.append(output.detach().cpu())

def capture_sibling(module, inputs, output):
    sibling_outputs.append(output.detach().cpu())

h1 = model.seq_dense.register_forward_hook(capture_sequence)
h2 = model.sibling_context_head.register_forward_hook(capture_sibling)

try:
    with torch.inference_mode():
        result = model(**kwargs)

        if not torch.is_tensor(result):
            raise RuntimeError("Unexpected original model output type")

        if len(sequence_outputs) != 1 or len(sibling_outputs) != 10:
            raise RuntimeError(
                f"Unexpected branch calls: sequence={len(sequence_outputs)}, "
                f"sibling={len(sibling_outputs)}"
            )

        sibling = model.ihq_pooling(
            torch.stack(sibling_outputs, dim=1)
        )

        references = {
            "sequence": sequence_outputs[0].numpy().astype(np.float32),
            "sibling": sibling.detach().cpu().numpy().astype(np.float32),
            "final": result.detach().cpu().numpy().astype(np.float32)
        }
finally:
    h1.remove()
    h2.remove()

for name, value in references.items():
    print(
        "ORIGINAL PYTORCH", name,
        "SHAPE:", value.shape,
        "FINITE:", bool(np.isfinite(value).all())
    )
    if not np.isfinite(value).all():
        raise SystemExit("STOP: Non-finite original reference")

if references["final"].shape != (1, 2048):
    raise SystemExit("STOP: Unexpected original model output shape")

output = base / "real_sanity_pytorch_same_input_verified.npz"

if output.exists():
    with np.load(output, allow_pickle=False) as old:
        identical = (
            set(old.files) == set(references)
            and all(np.array_equal(old[k], references[k]) for k in references)
        )
    if not identical:
        raise SystemExit(
            "STOP: Existing verified reference differs; not overwriting"
        )
    print("MATCHING VERIFIED REFERENCE ALREADY EXISTS")
else:
    np.savez(output, **references)
    print("NEW VERIFIED REFERENCE SAVED:", output)

print("ORIGINAL PYTORCH, MAX AND DS CODE UNCHANGED")
PY
